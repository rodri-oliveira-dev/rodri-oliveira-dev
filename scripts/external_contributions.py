#!/usr/bin/env python3
"""Collect every public pull request authored in third-party repositories."""

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
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
REPOSITORY_API_PREFIX = f"{API_ROOT}/repos/"
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
LOGIN_PATTERN = re.compile(r"[A-Za-z0-9-]+")
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
PAGE_SIZE = 100
MAX_SEARCH_RESULTS = 1000
INCOMPLETE_SEARCH_RETRY_DELAYS = (1.0, 2.0)
GITHUB_EPOCH = date(2008, 1, 1)
SCOPE = "All public PRs authored by this profile in repositories owned by others"


class CollectionError(Exception):
    """Expected failure: callers must preserve the last valid catalog."""


class IncompleteSearchError(CollectionError):
    """Search remained incomplete after bounded retries; split by date if possible."""


class GitHubAPI:
    """Small read-only REST client with bounded transient retries."""

    RETRYABLE_HTTP = frozenset((408, 429, 500, 502, 503, 504))

    def __init__(self, token: str, opener=None, *, max_attempts: int = 3,
                 timeout: float = 10.0, max_total_wait: float = 20.0,
                 max_elapsed: float = 50.0, sleep=None, monotonic=None,
                 wall_time=None, jitter=None):
        if not token:
            raise CollectionError("GITHUB_TOKEN is required; previous catalog unchanged")
        if (type(max_attempts) is not int or not 1 <= max_attempts <= 4
                or timeout <= 0 or max_total_wait < 0 or max_elapsed < timeout
                or max_total_wait > max_elapsed):
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
        if error is not None and error.headers is not None:
            retry_after = error.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    delay = float(retry_after)
                    if 0 <= delay < float("inf"):
                        return delay
                except ValueError:
                    try:
                        parsed = parsedate_to_datetime(retry_after)
                        if parsed.tzinfo:
                            return max(0.0, parsed.timestamp() - self._wall_time())
                    except (ValueError, TypeError, OverflowError):
                        pass
            reset = error.headers.get("X-RateLimit-Reset") if error.code == 429 else None
            if reset is not None:
                try:
                    return max(0.0, float(reset) - self._wall_time())
                except ValueError:
                    pass
        return min(10.0, 2 ** (attempt - 1) + max(0.0, min(1.0, self._jitter())))

    def get(self, path: str, params: dict[str, object]) -> dict:
        request = Request(
            API_ROOT + path + "?" + urlencode(params),
            headers={"Accept": "application/vnd.github+json",
                     "Authorization": "Bearer " + self._token,
                     "X-GitHub-Api-Version": "2022-11-28",
                     "User-Agent": "profile-external-contributions"},
        )
        started, waited = self._monotonic(), 0.0
        for attempt in range(1, self._max_attempts + 1):
            remaining = self._max_elapsed - (self._monotonic() - started)
            if remaining <= 0:
                raise CollectionError("GitHub API retry time budget exhausted")
            retry_error = None
            try:
                with self._open(request, timeout=min(self._timeout, remaining)) as response:
                    result = json.loads(response.read())
            except HTTPError as error:
                if error.code not in self.RETRYABLE_HTTP:
                    error.close()
                    raise CollectionError(f"GitHub API returned HTTP {error.code}") from None
                retry_error = error
            except (TimeoutError, URLError, ConnectionError) as error:
                if isinstance(error, URLError) and isinstance(error.reason, ssl.SSLError):
                    raise CollectionError("GitHub API TLS verification failed") from None
            except (OSError, ValueError):
                raise CollectionError("GitHub API request or response failed") from None
            else:
                if not isinstance(result, dict):
                    raise CollectionError("Unexpected GitHub API response format")
                return result
            if attempt == self._max_attempts:
                if retry_error is not None:
                    retry_error.close()
                raise CollectionError("GitHub API transient failure after retry limit")
            delay = self._retry_delay(attempt, retry_error)
            if retry_error is not None:
                retry_error.close()
            remaining = self._max_elapsed - (self._monotonic() - started)
            if delay > self._max_total_wait - waited or delay > remaining:
                raise CollectionError("GitHub API rate-limit or retry budget exceeded")
            self._sleep(delay)
            waited += delay
        raise CollectionError("GitHub API retry limit exceeded")


def load_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CollectionError("Configuration could not be read") from error
    if not isinstance(config, dict) or config.get("schema_version") != 2:
        raise CollectionError("Unsupported configuration schema")
    profile = config.get("profile")
    exclusions = config.get("exclude_repositories", [])
    if not isinstance(profile, str) or not LOGIN_PATTERN.fullmatch(profile):
        raise CollectionError("Invalid profile login")
    if (not isinstance(exclusions, list) or any(
            not isinstance(repo, str) or not REPO_PATTERN.fullmatch(repo)
            or repo.partition("/")[0].casefold() == profile.casefold()
            for repo in exclusions)
            or len({repo.casefold() for repo in exclusions}) != len(exclusions)):
        raise CollectionError("Invalid or duplicate repository exclusion")
    if set(config) - {"schema_version", "profile", "exclude_repositories", "exclusion_policy"}:
        raise CollectionError("Unknown configuration field")
    policy = config.get("exclusion_policy")
    if policy is not None and (not isinstance(policy, str) or not policy.strip()):
        raise CollectionError("Exclusion policy must be nonempty text")
    return config


def _timestamp(value: object, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not TIMESTAMP_PATTERN.fullmatch(value):
        raise CollectionError(f"GitHub returned invalid {field}")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise CollectionError(f"GitHub returned invalid {field}") from error
    return value


def _normalized_issue(issue: object, profile: str) -> tuple[str, dict]:
    if not isinstance(issue, dict):
        raise CollectionError("GitHub search returned an invalid item")
    repository_url = issue.get("repository_url")
    if not isinstance(repository_url, str) or not repository_url.startswith(REPOSITORY_API_PREFIX):
        raise CollectionError("GitHub returned an invalid repository URL")
    repository = repository_url[len(REPOSITORY_API_PREFIX):]
    author, pull = issue.get("user"), issue.get("pull_request")
    number, identifier, state = issue.get("number"), issue.get("id"), issue.get("state")
    if (not REPO_PATTERN.fullmatch(repository)
            or not isinstance(author, dict)
            or str(author.get("login", "")).casefold() != profile.casefold()
            or type(number) is not int or number < 1
            or type(identifier) is not int or identifier < 1
            or state not in ("open", "closed")
            or not isinstance(pull, dict) or "merged_at" not in pull):
        raise CollectionError("GitHub search returned an unexpected PR, author, or state")
    canonical = f"https://github.com/{repository}/pull/{number}"
    if issue.get("html_url") != canonical:
        raise CollectionError("GitHub returned a noncanonical pull-request URL")
    title = issue.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 1024 or any(c in title for c in "\r\n\x00"):
        raise CollectionError("GitHub returned an invalid pull-request title")
    merged_at = _timestamp(pull.get("merged_at"), "merged_at", nullable=True)
    created_at = _timestamp(issue.get("created_at"), "created_at")
    updated_at = _timestamp(issue.get("updated_at"), "updated_at")
    if merged_at is not None and state != "closed":
        raise CollectionError("GitHub returned an inconsistent merged PR")
    status = "merged" if merged_at else ("open" if state == "open" else "closed_unmerged")
    return repository, {"id": identifier, "number": number, "url": canonical,
                        "title": title, "status": status, "created_at": created_at,
                        "updated_at": updated_at, "merged_at": merged_at}


def _query(profile: str, start: date, end: date) -> str:
    return f"is:pr is:public author:{profile} -user:{profile} created:{start.isoformat()}..{end.isoformat()}"


def _search_page(api: GitHubAPI, profile: str, start: date, end: date,
                 page: int) -> dict:
    """Retry incomplete HTTP 200 search responses without accepting partial data."""
    params = {"q": _query(profile, start, end), "per_page": PAGE_SIZE, "page": page,
              "sort": "created", "order": "asc"}
    window = f"{start.isoformat()}..{end.isoformat()}"
    for attempt in range(1, len(INCOMPLETE_SEARCH_RETRY_DELAYS) + 2):
        payload = api.get("/search/issues", params)
        count, items = payload.get("total_count"), payload.get("items")
        incomplete = payload.get("incomplete_results")
        item_count = len(items) if isinstance(items, list) else "invalid"
        details = (f"window={window}, page={page}, total_count={count!r}, "
                   f"items_count={item_count}, incomplete_results={incomplete!r}")
        if (type(count) is not int or count < 0 or not isinstance(items, list)
                or type(incomplete) is not bool):
            raise CollectionError(f"GitHub search returned invalid results ({details})")
        if not incomplete:
            return payload
        if attempt > len(INCOMPLETE_SEARCH_RETRY_DELAYS):
            raise IncompleteSearchError(
                f"GitHub search remained incomplete after {attempt} attempts ({details})")
        delay = INCOMPLETE_SEARCH_RETRY_DELAYS[attempt - 1]
        print(f"GitHub search incomplete ({details}); retry {attempt + 1}/"
              f"{len(INCOMPLETE_SEARCH_RETRY_DELAYS) + 1} in {delay:g}s", file=sys.stderr)
        time.sleep(delay)
    raise AssertionError("Unreachable search retry state")


def _fetch_window(api: GitHubAPI, profile: str, start: date, end: date) -> tuple[int, list[dict]]:
    first = _search_page(api, profile, start, end, 1)
    count, items = first["total_count"], first["items"]
    if count > MAX_SEARCH_RESULTS:
        return count, []
    found = list(items)
    pages = (count + PAGE_SIZE - 1) // PAGE_SIZE
    for page in range(2, pages + 1):
        payload = _search_page(api, profile, start, end, page)
        if payload["total_count"] != count:
            raise CollectionError(
                f"GitHub pagination changed result count (window={start}..{end}, "
                f"page={page}, expected={count}, received={payload['total_count']})")
        found.extend(payload["items"])
    if len(found) != count:
        raise CollectionError(
            f"GitHub pagination returned {len(found)} of {count} declared results "
            f"(window={start}..{end})")
    return count, found


def _partitioned_search(api: GitHubAPI, profile: str, start: date, end: date) -> list[dict]:
    try:
        count, items = _fetch_window(api, profile, start, end)
    except IncompleteSearchError as error:
        # The incomplete parent's total_count cannot validate child totals.
        # Disjoint, fully validated date windows still cover the entire range.
        if start == end:
            raise CollectionError(
                f"GitHub search incomplete for a single day; cannot safely split: {error}"
            ) from error
        print(f"GitHub search incomplete for {start}..{end}; "
              "retrying via smaller date windows", file=sys.stderr)
        expected_count = None
    else:
        if count <= MAX_SEARCH_RESULTS:
            return items
        if start == end:
            raise CollectionError(f"More than 1000 PRs match {start}; interval cannot be safely split")
        expected_count = count
    midpoint = start + timedelta(days=(end - start).days // 2)
    left = _partitioned_search(api, profile, start, midpoint)
    right = _partitioned_search(api, profile, midpoint + timedelta(days=1), end)
    if expected_count is not None and len(left) + len(right) != expected_count:
        raise CollectionError("Temporal partitions disagree with their parent result count")
    return left + right


def _factual(snapshot: dict) -> dict:
    return {key: value for key, value in snapshot.items() if key != "last_successful_sync"}


def _previous_prs(previous: object, profile: str) -> dict[tuple[str, int], dict]:
    if previous is None:
        return {}
    if not isinstance(previous, dict) or previous.get("schema_version") != 2 or previous.get("profile") != profile:
        raise CollectionError("Previous catalog has an incompatible schema or profile")
    result = {}
    for project in previous.get("projects", []):
        if not isinstance(project, dict) or not isinstance(project.get("repository"), str):
            raise CollectionError("Previous catalog is invalid")
        for pr in project.get("pull_requests", []):
            if not isinstance(pr, dict) or type(pr.get("number")) is not int:
                raise CollectionError("Previous catalog contains an invalid PR")
            result[(project["repository"].casefold(), pr["number"])] = pr
    return result


def collect(config: dict, api: GitHubAPI, collected_at: datetime | None = None,
            previous: dict | None = None) -> dict:
    instant = collected_at or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise CollectionError("Collection timestamp must include a timezone")
    now = instant.astimezone(timezone.utc)
    raw = _partitioned_search(api, config["profile"], GITHUB_EPOCH, now.date())
    excluded = {repo.casefold() for repo in config.get("exclude_repositories", [])}
    found: dict[tuple[str, int], tuple[str, dict]] = {}
    for item in raw:
        repository, pr = _normalized_issue(item, config["profile"])
        if repository.partition("/")[0].casefold() == config["profile"].casefold():
            # Defense in depth if GitHub ignores the negative owner qualifier.
            continue
        if repository.casefold() in excluded:
            continue
        key = (repository.casefold(), pr["number"])
        prior = found.get(key)
        if prior is not None and prior != (repository, pr):
            raise CollectionError("GitHub returned conflicting duplicate PR data")
        found[key] = (repository, pr)
    known = {key: value for key, value in _previous_prs(previous, config["profile"]).items()
             if key[0] not in excluded}
    missing = set(known) - set(found)
    if missing:
        raise CollectionError("Previously published PRs disappeared; refusing silent removal")
    for key, (_, pr) in found.items():
        if key in known and known[key].get("id") != pr["id"]:
            raise CollectionError("A stable pull-request identity changed unexpectedly")

    repositories: dict[str, tuple[str, list[dict]]] = {}
    for (key, _), (repository, pr) in found.items():
        repositories.setdefault(key, (repository, []))[1].append(pr)
    projects = []
    total = {"pull_requests": 0, "merged": 0, "open": 0, "closed_unmerged": 0}
    for repository, prs in repositories.values():
        prs.sort(key=lambda pr: (pr["created_at"], pr["number"]), reverse=True)
        counts = {state: sum(pr["status"] == state for pr in prs)
                  for state in ("merged", "open", "closed_unmerged")}
        activity = max(pr["updated_at"] for pr in prs)
        projects.append({"repository": repository, "url": f"https://github.com/{repository}",
                         "activity_at": activity, "pull_requests": prs,
                         "totals": {"pull_requests": len(prs), **counts}})
        total["pull_requests"] += len(prs)
        for state in counts:
            total[state] += counts[state]
    projects.sort(key=lambda p: p["repository"].casefold())
    projects.sort(key=lambda p: p["activity_at"], reverse=True)
    result = {"schema_version": 2, "profile": config["profile"], "scope": SCOPE,
              "last_successful_sync": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
              "totals": {"repositories": len(projects), **total}, "projects": projects}
    if previous is not None and _factual(previous) == _factual(result):
        result["last_successful_sync"] = previous["last_successful_sync"]
    return result


def load_previous(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CollectionError("Previous catalog could not be read") from error


def write_snapshot(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(".github/external-contributions.json"))
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        queried_at = datetime.now(timezone.utc)
        result = collect(config, GitHubAPI(os.environ.get("GITHUB_TOKEN", "")), collected_at=queried_at,
                         previous=load_previous(args.previous))
        write_snapshot(args.output, result)
    except CollectionError as error:
        print(f"Collection failed: {error}; previous catalog unchanged", file=sys.stderr)
        return 1
    totals = result["totals"]
    print(f"Collected {totals['pull_requests']} public PRs in {totals['repositories']} external repositories")
    print("Query completed at " + queried_at.isoformat(timespec="seconds").replace("+00:00", "Z"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
