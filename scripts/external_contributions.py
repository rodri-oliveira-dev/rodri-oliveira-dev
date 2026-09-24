#!/usr/bin/env python3
"""Collect verifiable public PR data for curated third-party repositories.

No README is edited here. A later renderer consumes this complete JSON snapshot.
Run with GITHUB_TOKEN in the environment and --output pointing to a local file.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import ssl
import sys
import tempfile
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
LOGIN_PATTERN = re.compile(r"[A-Za-z0-9-]+")
PAGE_SIZE = 100
MAX_SEARCH_RESULTS = 1000


class CollectionError(Exception):
    """Expected failure. The caller must not publish a partial snapshot."""


class GitHubAPI:
    """Read-only GitHub client with bounded, transient-only retries.

    Maximum attempts, cumulative sleep and elapsed time are separate bounds:
    never retry before a server-requested delay if it exceeds the budget.
    """

    RETRYABLE_HTTP = frozenset((408, 429, 500, 502, 503, 504))

    def __init__(
        self, token: str, opener=None, *, max_attempts: int = 3,
        timeout: float = 10.0, max_total_wait: float = 20.0,
        max_elapsed: float = 50.0, sleep=None, monotonic=None,
        wall_time=None, jitter=None,
    ):
        if not token:
            raise CollectionError("GITHUB_TOKEN is required; no snapshot was generated")
        if (
            type(max_attempts) is not int or not 1 <= max_attempts <= 4
            or timeout <= 0 or max_total_wait < 0 or max_elapsed <= 0
            or max_elapsed < timeout or max_total_wait > max_elapsed
        ):
            raise ValueError("Invalid GitHub API retry configuration")
        self._token = token
        self._open = opener or urlopen
        self._max_attempts = max_attempts
        self._timeout = timeout
        self._max_total_wait = max_total_wait
        self._max_elapsed = max_elapsed
        self._sleep = sleep or time.sleep
        self._monotonic = monotonic or time.monotonic
        self._wall_time = wall_time or time.time
        self._jitter = jitter or random.random

    def _retry_delay(self, attempt: int, error: HTTPError | None) -> float:
        """Honor Retry-After / rate reset, otherwise bounded exponential jitter."""
        if error is not None:
            headers = error.headers
            retry_after = headers.get("Retry-After") if headers is not None else None
            if retry_after is not None:
                try:
                    seconds = float(retry_after)
                    if not 0 <= seconds < float("inf"):
                        raise ValueError
                    return seconds
                except ValueError:
                    try:
                        parsed = parsedate_to_datetime(retry_after)
                        if parsed.tzinfo is not None:
                            return max(0.0, parsed.timestamp() - self._wall_time())
                    except (ValueError, TypeError, OverflowError):
                        pass
            if error.code == 429 and headers is not None:
                reset = headers.get("X-RateLimit-Reset")
                if reset is not None:
                    try:
                        seconds = max(0.0, float(reset) - self._wall_time())
                        if seconds < float("inf"):
                            return seconds
                    except ValueError:
                        pass
        # Jittered backoff is bounded, including when the RNG is injectable.
        return min(10.0, (2 ** (attempt - 1)) + max(0.0, min(1.0, self._jitter())))

    def get(self, path: str, params: dict[str, object]) -> dict:
        url = API_ROOT + path + "?" + urlencode(params)
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + self._token,
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "profile-external-contributions",
            },
        )
        started = self._monotonic()
        waited = 0.0
        for attempt in range(1, self._max_attempts + 1):
            remaining = self._max_elapsed - (self._monotonic() - started)
            if remaining <= 0:
                raise CollectionError("GitHub API retry time budget exhausted; previous snapshot unchanged")
            retry_error = None
            try:
                with self._open(request, timeout=min(self._timeout, remaining)) as response:
                    result = json.loads(response.read())
            except HTTPError as error:
                if error.code not in self.RETRYABLE_HTTP:
                    raise CollectionError(
                        f"GitHub API returned HTTP {error.code}; the previous snapshot is unchanged"
                    ) from None
                retry_error = error
            except (TimeoutError, URLError, ConnectionError) as error:
                if isinstance(error, URLError) and isinstance(error.reason, ssl.SSLError):
                    raise CollectionError(
                        "GitHub API TLS verification failed; the previous snapshot is unchanged"
                    ) from None
            except (OSError, ValueError):
                # Unexpected local/configuration errors and invalid JSON are not transient.
                raise CollectionError(
                    "GitHub API request or response failed; the previous snapshot is unchanged"
                ) from None
            else:
                if not isinstance(result, dict):
                    raise CollectionError("Unexpected GitHub API response format")
                return result

            if attempt >= self._max_attempts:
                raise CollectionError(
                    "GitHub API transient failure after retry limit; previous snapshot unchanged"
                )
            delay = self._retry_delay(attempt, retry_error)
            remaining = self._max_elapsed - (self._monotonic() - started)
            if delay > self._max_total_wait - waited or delay > remaining:
                raise CollectionError(
                    "GitHub API rate limit or retry time budget exceeded; previous snapshot unchanged"
                )
            self._sleep(delay)
            waited += delay
        raise CollectionError("GitHub API retry limit exceeded; previous snapshot unchanged")

def load_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CollectionError("Curated project configuration could not be read") from error
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise CollectionError("Unsupported curated project configuration")
    profile, projects = config.get("profile"), config.get("projects")
    if not isinstance(profile, str) or not LOGIN_PATTERN.fullmatch(profile):
        raise CollectionError("Invalid profile login in configuration")
    if not isinstance(projects, list) or not projects:
        raise CollectionError("Curated projects list must be non-empty")
    seen_repos = set()
    for project in projects:
        if not isinstance(project, dict):
            raise CollectionError("Invalid curated project")
        repo = project.get("repository")
        if not isinstance(repo, str) or not REPO_PATTERN.fullmatch(repo):
            raise CollectionError("Invalid curated repository")
        owner = repo.partition("/")[0]
        if owner.casefold() == profile.casefold():
            raise CollectionError("Profile-owned repositories cannot be external projects")
        if repo.casefold() in seen_repos:
            raise CollectionError("Duplicate curated repository")
        seen_repos.add(repo.casefold())
        references = project.get("pull_requests")
        if not isinstance(references, list) or not references:
            raise CollectionError("Every curated project needs reference pull requests")
        numbers = [ref.get("number") for ref in references if isinstance(ref, dict)]
        if (
            len(numbers) != len(references)
            or any(type(number) is not int or number < 1 for number in numbers)
            or len(set(numbers)) != len(numbers)
        ):
            raise CollectionError("Invalid or duplicated curated PR number")
    return config


def _normalized_issue(issue: dict, repository: str, profile: str) -> dict:
    if not isinstance(issue, dict):
        raise CollectionError("Unexpected GitHub search item")
    expected_repo = f"{API_ROOT}/repos/{repository}".casefold()
    author = issue.get("user")
    number = issue.get("number")
    pr = issue.get("pull_request")
    if (
        str(issue.get("repository_url", "")).casefold() != expected_repo
        or not isinstance(author, dict)
        or str(author.get("login", "")).casefold() != profile.casefold()
        or type(number) is not int
        or number < 1
        or not isinstance(pr, dict)
        or "merged_at" not in pr
    ):
        raise CollectionError("GitHub search returned an unexpected PR or author")
    merged_at = pr["merged_at"]
    state = issue.get("state")
    if state not in ("open", "closed") or (
        merged_at is not None and (not isinstance(merged_at, str) or state != "closed")
    ):
        raise CollectionError("GitHub returned an inconsistent pull request state")
    status = "merged" if merged_at else ("open" if state == "open" else "closed_unmerged")
    return {
        "number": number,
        "url": f"https://github.com/{repository}/pull/{number}",
        "status": status,
        "merged_at": merged_at,
    }


def _repository_pull_requests(api: GitHubAPI, repository: str, profile: str) -> list[dict]:
    found: dict[int, dict] = {}
    total = None
    for page in range(1, (MAX_SEARCH_RESULTS // PAGE_SIZE) + 1):
        query = f"is:pr is:public author:{profile} repo:{repository}"
        payload = api.get(
            "/search/issues",
            {"q": query, "per_page": PAGE_SIZE, "page": page},
        )
        count, items = payload.get("total_count"), payload.get("items")
        if (
            type(count) is not int
            or count < 0
            or count > MAX_SEARCH_RESULTS
            or payload.get("incomplete_results") is not False
            or not isinstance(items, list)
            or (total is not None and total != count)
        ):
            raise CollectionError("GitHub search is incomplete or exceeds its result limit")
        total = count
        for issue in items:
            pr = _normalized_issue(issue, repository, profile)
            previous = found.get(pr["number"])
            if previous is not None and previous != pr:
                raise CollectionError("GitHub returned conflicting duplicate PR data")
            found[pr["number"]] = pr
        if len(items) < PAGE_SIZE:
            break
    if total is None or len(found) != total:
        raise CollectionError("GitHub pagination is incomplete; refusing partial statistics")
    return sorted(found.values(), key=lambda pr: pr["number"])


def collect(config: dict, api: GitHubAPI, collected_at: datetime | None = None) -> dict:
    profile = config["profile"]
    totals = {
        "authored_prs": 0,
        "merged_prs": 0,
        "open_prs": 0,
        "closed_unmerged_prs": 0,
        "repositories_with_merged_prs": 0,
    }
    projects = []
    latest_merged_at = None
    for curated in config["projects"]:
        repository = curated["repository"]
        prs = _repository_pull_requests(api, repository, profile)
        by_number = {pr["number"]: pr for pr in prs}
        references = [ref["number"] for ref in curated["pull_requests"]]
        if any(number not in by_number for number in references):
            raise CollectionError(
                "A curated reference PR was not returned by GitHub; refusing partial data"
            )
        merged = sum(pr["status"] == "merged" for pr in prs)
        opened = sum(pr["status"] == "open" for pr in prs)
        closed = sum(pr["status"] == "closed_unmerged" for pr in prs)
        totals["authored_prs"] += len(prs)
        totals["merged_prs"] += merged
        totals["open_prs"] += opened
        totals["closed_unmerged_prs"] += closed
        totals["repositories_with_merged_prs"] += int(merged > 0)
        dates = [pr["merged_at"] for pr in prs if pr["merged_at"]]
        if dates:
            candidate = max(dates)
            latest_merged_at = max(latest_merged_at or candidate, candidate)
        projects.append({
            "repository": repository,
            "authored_prs": len(prs),
            "merged_prs": merged,
            "open_prs": opened,
            "closed_unmerged_prs": closed,
            "reference_prs": [by_number[number] for number in references],
        })
    instant = collected_at or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise CollectionError("Collection timestamp must include a timezone")
    return {
        "schema_version": 1,
        "profile": profile,
        "scope": "Public PRs authored by this profile in the curated external repositories only",
        "repositories": len(projects),
        "collected_at": instant.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "latest_merged_at": latest_merged_at,
        "totals": totals,
        "projects": projects,
    }


def write_snapshot(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as file:
            temporary = Path(file.name)
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(".github/external-contributions.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        result = collect(config, GitHubAPI(os.environ.get("GITHUB_TOKEN", "")))
        write_snapshot(args.output, result)
    except CollectionError as error:
        print(f"Collection failed: {error}", file=sys.stderr)
        return 1
    print(f"Collected {result['totals']['authored_prs']} public PRs in {result['repositories']} curated external repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
