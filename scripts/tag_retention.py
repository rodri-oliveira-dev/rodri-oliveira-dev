#!/usr/bin/env python3
"""Prune profile release tags older than three calendar months.

Only stable vMAJOR.MINOR.PATCH tags with a published GitHub Release are managed.
Releases themselves are never deleted.
"""

import argparse
import calendar
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

STABLE_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def subtract_months(value: datetime, months: int) -> datetime:
    index = value.year * 12 + value.month - 1 - months
    year, month_zero = divmod(index, 12)
    month = month_zero + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def parse_github_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def find_expired_tags(refs: list[dict], releases: list[dict], now: datetime) -> list[tuple[str, str]]:
    """Return (tag, publication date) for eligible tags, oldest first."""
    if now.tzinfo is None:
        raise ValueError("Current time must be timezone-aware")
    cutoff = subtract_months(now.astimezone(timezone.utc), 3)
    available = {
        ref["ref"][len("refs/tags/"):]
        for ref in refs
        if isinstance(ref.get("ref"), str) and ref["ref"].startswith("refs/tags/")
    }
    managed = [
        release for release in releases
        if STABLE_TAG.fullmatch(release.get("tag_name", ""))
        and release["tag_name"] in available
        and release.get("published_at")
        and not release.get("draft")
    ]
    if not managed:
        return []

    # The release workflow resolves the next version from existing tags.
    # Keep the greatest version even when the repository is dormant.
    latest = max(managed, key=lambda release: tuple(
        int(part) for part in release["tag_name"][1:].split(".")
    ))["tag_name"]
    expired = [
        (release["tag_name"], release["published_at"])
        for release in managed
        if release["tag_name"] != latest
        and not release.get("immutable", False)
        and parse_github_date(release["published_at"]) < cutoff
    ]
    return sorted(expired, key=lambda item: (item[1], item[0]))


def github_api(repo: str, token: str, path: str, method: str = "GET"):
    url = "https://api.github.com/repos/" + quote(repo, safe="/") + path
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "User-Agent": "profile-tag-retention",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method=method,
    )
    try:
        with urlopen(request, timeout=30) as response:
            if method == "DELETE":
                return None
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError("GitHub API request failed: HTTP " + str(exc.code) + " (" + method + " " + path + ")") from exc


def list_releases(repo: str, token: str) -> list[dict]:
    result = []
    page = 1
    while True:
        batch = github_api(repo, token, "/releases?per_page=100&page=" + str(page))
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected GitHub releases response")
        result.extend(batch)
        if len(batch) < 100:
            return result
        page += 1


def run(dry_run: bool, now: datetime | None = None) -> int:
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Unexpected repository name")
    now = now or datetime.now(timezone.utc)
    refs = github_api(repo, token, "/git/matching-refs/tags")
    releases = list_releases(repo, token)
    if not isinstance(refs, list):
        raise RuntimeError("Unexpected Git tag references response")

    expired = find_expired_tags(refs, releases, now)
    cutoff = subtract_months(now.astimezone(timezone.utc), 3)
    messages = [
        "## Tag retention (three calendar months)",
        "",
        "Cutoff (UTC): " + cutoff.isoformat(),
        "Mode: " + ("dry run (no deletions)" if dry_run else "delete expired tags"),
        "Candidates: " + str(len(expired)),
        "",
    ]
    if not expired:
        messages.append("No expired managed tags found.")
    for tag, published_at in expired:
        messages.append("- " + tag + " (published " + published_at + ")")
        if not dry_run:
            # Only a validated stable tag name reaches the destructive API call.
            github_api(repo, token, "/git/refs/tags/" + quote(tag, safe=""), method="DELETE")

    messages.extend(["", "GitHub Releases are preserved; only Git tag refs are removed."])
    report = "\n".join(messages) + "\n"
    print(report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(report)
    return len(expired)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show candidate tags without deleting them")
    args = parser.parse_args()
    try:
        run(dry_run=args.dry_run)
    except (ValueError, RuntimeError, KeyError) as error:
        print("Tag retention failed: " + str(error), file=sys.stderr)
        sys.exit(1)
