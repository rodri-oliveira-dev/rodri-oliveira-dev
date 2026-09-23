#!/usr/bin/env python3
"""Discover public PRs in external repositories not yet in the curated profile.

This is a read-only discovery report. Editorial descriptions and curated
projects are never added automatically to the profile README.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.external_contributions import (
        CollectionError,
        GitHubAPI,
        MAX_SEARCH_RESULTS,
        PAGE_SIZE,
        REPO_PATTERN,
        _normalized_issue,
        load_config,
        write_snapshot,
    )
except ModuleNotFoundError:
    from external_contributions import (
        CollectionError,
        GitHubAPI,
        MAX_SEARCH_RESULTS,
        PAGE_SIZE,
        REPO_PATTERN,
        _normalized_issue,
        load_config,
        write_snapshot,
    )


REPOSITORY_API_PREFIX = "https://api.github.com/repos/"


def discover(config: dict, api: GitHubAPI, collected_at: datetime | None = None) -> dict:
    """Return only uncurated third-party repositories with public authored PRs.

    GitHub Search indexes at most 1000 entries per query; fail closed if results
    are incomplete instead of incorrectly announcing that no new work exists.
    """
    login = config["profile"]
    curated = {item["repository"].casefold() for item in config["projects"]}
    query = f"is:pr is:public author:{login} -user:{login}"
    found: dict[tuple[str, int], dict] = {}
    repository_names: dict[str, str] = {}
    total = None
    for page in range(1, MAX_SEARCH_RESULTS // PAGE_SIZE + 1):
        data = api.get(
            "/search/issues",
            {"q": query, "per_page": PAGE_SIZE, "page": page},
        )
        count, items = data.get("total_count"), data.get("items")
        if (
            type(count) is not int
            or count < 0
            or count > MAX_SEARCH_RESULTS
            or data.get("incomplete_results") is not False
            or not isinstance(items, list)
            or (total is not None and total != count)
        ):
            raise CollectionError("External discovery search is incomplete or exceeds its result limit")
        total = count
        for item in items:
            if not isinstance(item, dict):
                raise CollectionError("External discovery received an invalid PR")
            url = item.get("repository_url")
            if not isinstance(url, str) or not url.startswith(REPOSITORY_API_PREFIX):
                raise CollectionError("External discovery received an invalid repository URL")
            repository = url[len(REPOSITORY_API_PREFIX):]
            if not REPO_PATTERN.fullmatch(repository):
                raise CollectionError("External discovery received an invalid repository name")
            if repository.partition("/")[0].casefold() == login.casefold():
                # Defense in depth: even if the search qualifier is ignored,
                # projects owned by the profile never become candidates.
                continue
            pr = _normalized_issue(item, repository, login)
            repository_names.setdefault(repository.casefold(), repository)
            key = (repository.casefold(), pr["number"])
            previous = found.get(key)
            if previous is not None and previous != pr:
                raise CollectionError("External discovery received conflicting duplicate PR data")
            found[key] = pr
        if len(items) < PAGE_SIZE:
            break
    if total is None or len(found) != total:
        raise CollectionError("External discovery pagination is incomplete; no report was published")

    by_repository: dict[str, list[dict]] = {}
    for (repository, _), pr in found.items():
        if repository in curated:
            continue
        by_repository.setdefault(repository_names[repository], []).append(pr)
    candidates = [
        {
            "repository": repository,
            "pull_requests": sorted(prs, key=lambda pr: pr["number"]),
        }
        for repository, prs in sorted(by_repository.items())
    ]
    instant = collected_at or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise CollectionError("External discovery requires a timezone-aware collection date")
    return {
        "schema_version": 1,
        "profile": login,
        "scope": "Public authored PRs in repositories not owned by the profile and not yet curated",
        "collected_at": instant.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "matching_public_prs": total,
        "candidate_repositories": candidates,
    }


def main(argv: list[str] | None = None) -> int:
    """Write a complete discovery report atomically, or leave the old file unchanged."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(".github/external-contributions.json"))
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)
    try:
        config = load_config(options.config)
        result = discover(config, GitHubAPI(os.environ.get("GITHUB_TOKEN", "")))
        write_snapshot(options.output, result)
    except CollectionError as error:
        print(f"External discovery failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Found {len(result['candidate_repositories'])} uncurated external repositories. "
        "Review the report before adding projects to the README."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
