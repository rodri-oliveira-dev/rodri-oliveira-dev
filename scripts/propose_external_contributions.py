#!/usr/bin/env python3
"""Create or safely refresh the single bot-owned catalog update pull request."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from scripts.external_contributions import REPO_PATTERN
    from scripts.render_external_contributions import (
        RenderError, load_snapshot, render_catalog, validate_snapshot,
    )
except ModuleNotFoundError:
    from external_contributions import REPO_PATTERN
    from render_external_contributions import (
        RenderError, load_snapshot, render_catalog, validate_snapshot,
    )

MANAGED_FILES = (".github/external-contributions-catalog.json",
                 "docs/open-source-contributions.md",
                 "docs/open-source-contributions.en.md",
                 "docs/open-source-contributions.es.md")
BRANCH = "automation/external-contributions"
BOT_LOGIN = "github-actions[bot]"
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
RUN_PATTERN = re.compile(r"[1-9][0-9]*")
WORKFLOWS = ("validate-profile.yml", "spell-check.yml")


class ProposalError(Exception):
    """Unsafe or failed proposal operation."""


class Commands:
    def run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, text=True, capture_output=True, timeout=60, check=False)


def required(command: Commands, *args: str) -> str:
    result = command.run(*args)
    if result.returncode:
        raise ProposalError(f"Command failed safely: {args[0]} {args[1] if len(args) > 1 else ''}")
    return result.stdout.strip()


def _json(command: Commands, *args: str):
    try:
        return json.loads(required(command, *args))
    except ValueError as error:
        raise ProposalError("GitHub CLI returned invalid JSON") from error


def eligible(event: str, ref: str, publish: str) -> bool:
    return ref == "refs/heads/main" and (event == "schedule" or
            (event == "workflow_dispatch" and publish.casefold() == "true"))


def verify_main(command: Commands, sha: str) -> bool:
    result = command.run("git", "ls-remote", "--exit-code", "origin", "refs/heads/main")
    return result.returncode == 0 and result.stdout.split()[0] == sha


def verified_preview(preview_dir: Path) -> dict[str, bytes]:
    snapshot_path = preview_dir / MANAGED_FILES[0]
    snapshot = load_snapshot(snapshot_path)
    expected = {MANAGED_FILES[0]: snapshot_path.read_bytes(),
                MANAGED_FILES[1]: render_catalog(snapshot, "pt").encode(),
                MANAGED_FILES[2]: render_catalog(snapshot, "en").encode(),
                MANAGED_FILES[3]: render_catalog(snapshot, "es").encode()}
    for name, content in expected.items():
        path = preview_dir / name
        if not path.is_file() or path.stat().st_size > 8_000_000 or path.read_bytes() != content:
            raise ProposalError(f"Preview artifact is missing, too large, or inconsistent: {name}")
    return expected


def changed_preview(preview_dir: Path) -> dict[str, bytes]:
    expected = verified_preview(preview_dir)
    return {name: content for name, content in expected.items()
            if not Path(name).exists() or Path(name).read_bytes() != content}


def existing_proposal(command: Commands, repository: str) -> dict | None:
    pulls = _json(command, "gh", "pr", "list", "--repo", repository, "--state", "open",
                  "--base", "main", "--head", BRANCH, "--limit", "100", "--json",
                  "number,author,headRefName,headRefOid,headRepository,isCrossRepository")
    if not isinstance(pulls, list):
        raise ProposalError("Open pull-request query returned an invalid response")
    candidates = [pr for pr in pulls if isinstance(pr, dict) and pr.get("headRefName") == BRANCH]
    if len(candidates) > 1:
        raise ProposalError("Multiple automation pull requests use the managed branch")
    if not candidates:
        return None
    pr = candidates[0]
    author, head_repo = pr.get("author"), pr.get("headRepository")
    if (not isinstance(author, dict) or author.get("login") != BOT_LOGIN
            or not isinstance(head_repo, dict) or head_repo.get("nameWithOwner") != repository
            or pr.get("isCrossRepository") is not False
            or type(pr.get("number")) is not int or not SHA_PATTERN.fullmatch(str(pr.get("headRefOid", "")))):
        raise ProposalError("Managed branch is attached to an untrusted pull request")
    return {"number": pr["number"], "sha": pr["headRefOid"], "branch": BRANCH}


def _verify_existing_head(command: Commands, repository: str, proposal: dict) -> None:
    number, sha = proposal["number"], proposal["sha"]
    pull = _json(command, "gh", "api", f"repos/{repository}/pulls/{number}")
    if (not isinstance(pull, dict) or pull.get("state") != "open"
            or not isinstance(pull.get("head"), dict) or pull["head"].get("sha") != sha):
        raise ProposalError("Automation PR changed while it was being inspected")
    names = required(command, "gh", "pr", "diff", str(number), "--repo", repository, "--name-only")
    changed = {line.strip() for line in names.splitlines() if line.strip()}
    if not changed or not changed <= set(MANAGED_FILES):
        raise ProposalError("Automation PR contains unexpected manual file changes")
    commit = _json(command, "gh", "api", f"repos/{repository}/git/commits/{sha}")
    author = commit.get("author") if isinstance(commit, dict) else None
    committer = commit.get("committer") if isinstance(commit, dict) else None
    for identity in (author, committer):
        if (not isinstance(identity, dict) or identity.get("name") != BOT_NAME
                or identity.get("email") != BOT_EMAIL):
            raise ProposalError("Automation PR head was not committed by the expected bot identity")


def _apply_and_commit(command: Commands, contents: dict[str, bytes], message: str) -> bool:
    for name, data in contents.items():
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    required(command, "git", "add", "--", *MANAGED_FILES)
    staged = command.run("git", "diff", "--cached", "--quiet", "--", *MANAGED_FILES)
    if staged.returncode == 0:
        return False
    if staged.returncode != 1:
        raise ProposalError("Could not verify staged catalog changes")
    required(command, "git", "-c", f"user.name={BOT_NAME}", "-c", f"user.email={BOT_EMAIL}",
             "commit", "-m", message)
    return True


def _dispatch_checks(command: Commands, repository: str) -> bool:
    return all(command.run("gh", "workflow", "run", workflow, "--repo", repository,
                           "--ref", BRANCH).returncode == 0 for workflow in WORKFLOWS)


def _same_catalog_facts(current: dict, proposed: dict) -> bool:
    """Compare published facts while ignoring only the synchronization timestamp."""
    current_facts = {key: value for key, value in current.items()
                     if key != "last_successful_sync"}
    proposed_facts = {key: value for key, value in proposed.items()
                      if key != "last_successful_sync"}
    return current_facts == proposed_facts


def _preview_matches_current_catalog(contents: dict[str, bytes]) -> bool:
    current = load_snapshot(Path(MANAGED_FILES[0]))
    try:
        proposed = json.loads(contents[MANAGED_FILES[0]].decode("utf-8"))
    except (KeyError, UnicodeError, ValueError) as error:
        raise ProposalError("Preview catalog is missing or invalid") from error
    return _same_catalog_facts(current, validate_snapshot(proposed))


def _ensure_managed_branch_absent(command: Commands) -> None:
    remote = command.run("git", "ls-remote", "--exit-code", "origin", f"refs/heads/{BRANCH}")
    if remote.returncode == 0:
        raise ProposalError(
            "Managed branch exists without an open PR; review and delete it before retrying"
        )
    if remote.returncode != 2:
        raise ProposalError("Could not inspect the managed branch on origin")


def propose(command: Commands, *, preview_dir: Path, repository: str, sha: str,
            run_id: str, run_attempt: str, event: str, ref: str,
            publish: str) -> tuple[str, str | None]:
    if not eligible(event, ref, publish):
        return "skipped_not_authorized", None
    if (not REPO_PATTERN.fullmatch(repository) or not SHA_PATTERN.fullmatch(sha)
            or not RUN_PATTERN.fullmatch(run_id) or not RUN_PATTERN.fullmatch(run_attempt)):
        raise ProposalError("Invalid repository, commit, or workflow-run identity")
    if required(command, "git", "rev-parse", "HEAD") != sha:
        raise ProposalError("Publication checkout does not match the rendered main commit")
    changed = changed_preview(preview_dir)
    pending = existing_proposal(command, repository)
    if pending is None and not changed:
        return "unchanged", None
    if not verify_main(command, sha):
        return "main_advanced", None

    if pending is not None:
        _verify_existing_head(command, repository, pending)
        required(command, "git", "fetch", "--no-tags", "origin", f"refs/heads/{BRANCH}")
        if required(command, "git", "rev-parse", "FETCH_HEAD") != pending["sha"]:
            raise ProposalError("Automation branch advanced during inspection")
        required(command, "git", "switch", "--detach", pending["sha"])
        contents = verified_preview(preview_dir)
        if _preview_matches_current_catalog(contents):
            return "existing_pr_current", str(pending["number"])
        if not _apply_and_commit(command, contents, "docs: refresh complete external contributions catalog"):
            return "existing_pr_current", str(pending["number"])
        if not verify_main(command, sha):
            return "main_advanced", str(pending["number"])
        required(command, "git", "push", "origin", f"HEAD:refs/heads/{BRANCH}")
        return ("updated" if _dispatch_checks(command, repository) else "checks_unavailable"), str(pending["number"])

    _ensure_managed_branch_absent(command)
    required(command, "git", "switch", "-c", BRANCH)
    contents = verified_preview(preview_dir)
    if not _apply_and_commit(command, contents, "docs: refresh complete external contributions catalog"):
        return "unchanged", None
    if not verify_main(command, sha):
        return "main_advanced", None
    required(command, "git", "push", "origin", f"HEAD:refs/heads/{BRANCH}")
    if not verify_main(command, sha):
        return "main_advanced", BRANCH
    result = command.run("gh", "pr", "create", "--repo", repository, "--base", "main",
                         "--head", BRANCH,
                         "--title", "docs: refresh complete external contributions catalog",
                         "--body", "Automated, complete refresh of public external pull requests. The collection is validated and rendered in PT-BR, English, and Latin American Spanish. Please review links, states, catalog integrity, and required checks before merging.")
    if result.returncode:
        raise ProposalError("Pull-request creation failed; the pushed branch was preserved")
    return ("created" if _dispatch_checks(command, repository) else "checks_unavailable"), BRANCH


def main(argv: list[str] | None = None, command: Commands | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--publish", default="false")
    args = parser.parse_args(argv)
    try:
        state, reference = propose(command or Commands(), preview_dir=args.preview_dir,
                                   repository=args.repo, sha=args.sha, run_id=args.run_id,
                                   run_attempt=args.run_attempt, event=args.event,
                                   ref=args.ref, publish=args.publish)
    except (ProposalError, RenderError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Update proposal failed: {error}", file=sys.stderr)
        return 1
    messages = {"skipped_not_authorized": "Publication denied outside eligible main runs.",
                "unchanged": "No substantive catalog changes.",
                "main_advanced": "main advanced; rerun from its latest commit.",
                "existing_pr_current": "The existing automation PR already matches the catalog.",
                "updated": "The existing trusted automation PR was updated by fast-forward.",
                "created": "A new automation PR was created for review.",
                "checks_unavailable": "The PR was updated, but one or more checks could not be dispatched."}
    print(messages[state])
    if reference:
        print(f"Proposal reference: {reference}")
    if state == "checks_unavailable":
        print(f"::warning::{messages[state]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
