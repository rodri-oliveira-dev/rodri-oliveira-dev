"""Versioned editorial history for public external-contribution discovery.

Read-only. A pending entry means "previously observed, awaiting a human
decision", not approval to display it in either README.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

try:
    from scripts.external_contributions import CollectionError, REPO_PATTERN
except ModuleNotFoundError:
    from external_contributions import CollectionError, REPO_PATTERN


STATES = frozenset(("pending", "ignored", "selected"))
PR_STATES = frozenset(("open", "merged", "closed_unmerged"))
NUMBER_PATTERN = re.compile(r"[1-9][0-9]*")


def load_review_registry(path: Path, config: dict) -> dict:
    """Validate all editorial entries and aliases before querying GitHub."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CollectionError("External review registry is missing or invalid") from error
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or data.get("profile") != config["profile"]
        or not isinstance(data.get("projects"), list)
    ):
        raise CollectionError("External review registry has an invalid schema")
    curated = {p["repository"].casefold() for p in config["projects"]}
    names = set()
    for item in data["projects"]:
        if not isinstance(item, dict):
            raise CollectionError("External review registry contains invalid entries")
        name = item.get("repository")
        state = item.get("status")
        if not isinstance(name, str) or not REPO_PATTERN.fullmatch(name) or not isinstance(state, str) or state not in STATES:
            raise CollectionError("External review registry has an invalid repository or status")
        if name.partition("/")[0].casefold() == config["profile"].casefold():
            raise CollectionError("Profile-owned repositories cannot be review candidates")
        if (name.casefold() in curated) != (state == "selected"):
            raise CollectionError("Selected projects must match the approved curated configuration")
        observed = item.get("observed_prs")
        if not isinstance(observed, dict):
            raise CollectionError("External review registry requires a PR baseline")
        for number, status in observed.items():
            if not isinstance(number, str) or not NUMBER_PATTERN.fullmatch(number) or not isinstance(status, str) or status not in PR_STATES:
                raise CollectionError("External review registry contains invalid PR baseline")
        timestamp = item.get("observed_at")
        try:
            if not isinstance(timestamp, str) or date.fromisoformat(timestamp).isoformat() != timestamp:
                raise ValueError
        except ValueError as error:
            raise CollectionError("External review registry has an invalid observation date") from error
        if item.get("decision_date") is not None:
            try:
                when = item["decision_date"]
                if not isinstance(when, str) or date.fromisoformat(when).isoformat() != when:
                    raise ValueError
            except ValueError as error:
                raise CollectionError("External review registry has an invalid decision date") from error
        if state in ("ignored", "selected") and item.get("decision_date") is None:
            raise CollectionError("Reviewed decisions need a documented decision date")
        reason = item.get("reason")
        if reason is not None and (not isinstance(reason, str) or not reason.strip()):
            raise CollectionError("External review registry reason must be nonempty text")
        aliases = item.get("aliases", [])
        if not isinstance(aliases, list) or any(
            not isinstance(alias, str) or not REPO_PATTERN.fullmatch(alias) for alias in aliases
        ):
            raise CollectionError("External review registry contains invalid repository aliases")
        for name_or_alias in [name, *aliases]:
            key = name_or_alias.casefold()
            if key in names or (key in curated and not (state == "selected" and key == name.casefold())):
                raise CollectionError("External review registry contains duplicate or conflicting aliases")
            if name_or_alias.partition("/")[0].casefold() == config["profile"].casefold():
                raise CollectionError("Profile-owned aliases cannot be review candidates")
            names.add(key)
        if len({alias.casefold() for alias in [name, *aliases]}) != len([name, *aliases]):
            raise CollectionError("External review registry contains duplicate aliases")
    return data


def classify_candidates(discovery: dict, registry: dict, config: dict) -> dict:
    """Classify each PR only against a previously reviewed versioned baseline."""
    known = {}
    for item in registry["projects"]:
        for name in [item["repository"], *item.get("aliases", [])]:
            known[name.casefold()] = item
    fresh, changed, pending, ignored = [], [], [], []
    for candidate in discovery["candidate_repositories"]:
        item = known.get(candidate["repository"].casefold())
        if item is None:
            fresh.append(candidate)
            continue
        if item["status"] == "selected":
            # Curated project renamed/transferred under an explicitly recorded
            # alias. Do not silently treat it as a new candidate or include it in
            # curated totals. The curator must update external-contributions.json.
            changed.append({
                **candidate, "review_status": "selected",
                "change_reason": "selected_repository_moved",
                "review_repository": item["repository"],
            })
            continue
        if item["status"] == "ignored":
            ignored.append(item["repository"])
            continue
        now = {str(pr["number"]): pr["status"] for pr in candidate["pull_requests"]}
        before = item["observed_prs"]
        if now != before:
            added = sorted(int(n) for n in now.keys() - before.keys())
            changed_status = sorted(int(n) for n in now.keys() & before.keys() if now[n] != before[n])
            missing = sorted(int(n) for n in before.keys() - now.keys())
            changed.append({
                **candidate, "review_status": "pending", "review_repository": item["repository"],
                "change_reason": "activity_changed",
                "new_pr_numbers": added, "updated_pr_numbers": changed_status,
                "missing_pr_numbers": missing,
            })
        else:
            pending.append(item["repository"])
    discovery["review"] = {
        "schema_version": 1,
        "new_candidates": fresh,
        "changed_candidates": changed,
        "known_pending_repositories": sorted(pending, key=str.casefold),
        "ignored_repositories": sorted(ignored, key=str.casefold),
        "untracked_count": len(fresh),
        "changed_count": len(changed),
        "tracked_pending_count": len(pending),
        "ignored_count": len(ignored),
        "review_file": ".github/external-contributions-review.json",
    }
    return discovery
