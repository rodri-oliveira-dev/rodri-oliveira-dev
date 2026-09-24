#!/usr/bin/env python3
"""Propose a reviewed README-only update; never write to the protected main branch.

The GitHub Actions job gates publication independently. This module repeats
that eligibility check so the exact publication logic can be unit tested.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from scripts.render_external_contributions import END, START
except ModuleNotFoundError:
    from render_external_contributions import END, START


REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
RUN_PATTERN = re.compile(r"[0-9]+")
WORKFLOWS = ("validate-profile.yml", "spell-check.yml")


class ProposalError(Exception):
    """Publication cannot proceed safely; existing main is not changed."""


class Commands:
    """Execute GitHub CLI/git with argument arrays, avoiding shell interpolation."""

    def run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args), check=False, text=True, capture_output=True, timeout=60
        )


def eligible(event: str, ref: str, publish: str) -> bool:
    """Allow publishing only from a main schedule or explicit main dispatch."""
    return ref == "refs/heads/main" and (
        event == "schedule"
        or (event == "workflow_dispatch" and publish.casefold() == "true")
    )


def required(command: Commands, *args: str) -> str:
    """Run a command and fail with a sanitized message rather than raw CLI output."""
    result = command.run(*args)
    if result.returncode != 0:
        raise ProposalError(f"Required command failed: {args[0]} {args[1]}")
    return result.stdout.strip()


def current_main(command: Commands) -> str:
    """Read the remote default branch SHA without modifying any branch."""
    result = required(command, "git", "ls-remote", "--exit-code", "origin", "refs/heads/main")
    match = re.fullmatch(r"([0-9a-f]{40})\s+refs/heads/main", result)
    if match is None:
        raise ProposalError("Could not verify the remote main commit")
    return match.group(1)


def verify_main(command: Commands, sha: str) -> bool:
    """Reject a proposal based on an obsolete README snapshot."""
    return current_main(command) == sha


def _bounded(text: str) -> tuple[str, str]:
    """Extract the bytes of content outside the single managed block."""
    if text.count(START) != 1 or text.count(END) != 1:
        raise ProposalError("Preview README has absent or duplicated markers")
    a, b = text.index(START), text.index(END)
    if a >= b:
        raise ProposalError("Preview README markers are reversed")
    return text[: a + len(START)], text[b:]


def changed_preview(preview_dir: Path) -> dict[str, bytes]:
    """Validate both preview files before touching the working tree.

    No edit outside the managed markers is allowed, including metadata/footers.
    """
    changed: dict[str, bytes] = {}
    for filename in ("README.md", "README.en.md"):
        source = Path(filename)
        proposed = preview_dir / filename
        try:
            original_bytes = source.read_bytes()
            preview_bytes = proposed.read_bytes()
            original, preview = original_bytes.decode("utf-8"), preview_bytes.decode("utf-8")
        except (OSError, UnicodeError) as error:
            raise ProposalError(f"Missing or unreadable {filename} preview") from error
        if _bounded(original) != _bounded(preview):
            raise ProposalError(f"Preview {filename} changes text outside the contribution markers")
        if original_bytes != preview_bytes:
            changed[filename] = preview_bytes
    return changed


AUTOMATION_BRANCH = re.compile(r"automation/external-contributions-[0-9]+(?:-[0-9]+)?")


def _json_command(command: Commands, *args: str) -> object:
    """Decode CLI output without leaking GitHub response contents into logs."""
    result = required(command, *args)
    try:
        return json.loads(result)
    except ValueError as error:
        raise ProposalError("GitHub returned invalid JSON for an existing proposal") from error


def existing_proposal(command: Commands, repository: str) -> dict | None:
    """Locate an actual same-repository proposal, ignoring similarly named forks.

    Return an attention state on a close/delete race. Never turn uncertainty into
    permission to open another pull request.
    """
    prs = _json_command(
        command, "gh", "pr", "list", "--repo", repository, "--base", "main",
        "--state", "open", "--limit", "100", "--json", "headRefName,number",
    )
    if not isinstance(prs, list) or len(prs) >= 100:
        raise ProposalError("Cannot reliably inspect all open update pull requests")
    candidates = []
    for entry in prs:
        if not isinstance(entry, dict):
            raise ProposalError("GitHub returned malformed pull request listing")
        name = entry.get("headRefName")
        number = entry.get("number")
        if not isinstance(name, str) or not name.startswith("automation/external-contributions-"):
            continue
        if not AUTOMATION_BRANCH.fullmatch(name) or type(number) is not int or number < 1:
            raise ProposalError("Unexpected automated update pull request metadata")
        metadata = _json_command(command, "gh", "api", f"repos/{repository}/pulls/{number}")
        if not isinstance(metadata, dict):
            raise ProposalError("GitHub returned invalid update PR metadata")
        head = metadata.get("head")
        base = metadata.get("base")
        if not isinstance(head, dict) or not isinstance(base, dict):
            raise ProposalError("GitHub returned incomplete update PR metadata")
        head_repo = head.get("repo")
        if not isinstance(head_repo, dict):
            # A closed or deleted source repository needs manual attention.
            raise ProposalError("Update pull request source repository is missing")
        if str(head_repo.get("full_name", "")).casefold() != repository.casefold():
            # A fork may use the same branch name; do not block a repository-owned PR.
            continue
        if metadata.get("number") != number or base.get("ref") != "main":
            raise ProposalError("Update pull request metadata changed during inspection")
        if metadata.get("state") != "open" or head.get("ref") != name:
            return {"number": number, "state": "attention"}
        oid = head.get("sha")
        if not isinstance(oid, str) or SHA_PATTERN.fullmatch(oid) is None:
            return {"number": number, "state": "attention"}
        candidates.append({"number": number, "sha": oid, "branch": name})
    if len(candidates) > 1:
        return {"number": candidates[0]["number"], "state": "attention"}
    return candidates[0] if candidates else None


def _head_readme(command: Commands, repository: str, sha: str, filename: str) -> bytes:
    """Read README from immutable PR-head SHA; never check out or modify the PR."""
    result = _json_command(
        command, "gh", "api", f"repos/{repository}/contents/{filename}?ref={sha}",
    )
    if not isinstance(result, dict) or result.get("encoding") != "base64":
        raise ProposalError("Update PR README is unavailable or unexpectedly encoded")
    content = result.get("content")
    if not isinstance(content, str) or len(content) > 4_000_000:
        raise ProposalError("Update PR README is invalid or too large")
    try:
        return base64.b64decode("".join(content.split()), validate=True)
    except (ValueError, binascii.Error) as error:
        raise ProposalError("Update PR README contains invalid base64 data") from error


def inspect_existing(
    command: Commands, repository: str, proposal: dict, preview_dir: Path, sha: str,
) -> str:
    """Select an explicit human-review state; never rewrite an open PR."""
    if proposal.get("state") == "attention":
        return "existing_pr_attention"
    if not verify_main(command, sha):
        return "main_advanced"
    number, head_sha = proposal["number"], proposal["sha"]
    try:
        # Reading an immutable commit alone cannot detect a deleted PR branch.
        # Verify that the named branch still exists and points to the inspected SHA.
        branch = proposal["branch"]
        live_ref = _json_command(
            command, "gh", "api", f"repos/{repository}/git/ref/heads/{branch}",
        )
        if not isinstance(live_ref, dict) or not isinstance(live_ref.get("object"), dict):
            return "existing_pr_attention"
        if live_ref["object"].get("sha") != head_sha:
            return "existing_pr_attention"
        needs_refresh = False
        modified_outside_block = False
        for filename in ("README.md", "README.en.md"):
            previous = Path(filename).read_bytes()
            proposed = (preview_dir / filename).read_bytes()
            current = _head_readme(command, repository, head_sha, filename)
            # The approved preview is checked separately against current main.
            if _bounded(previous.decode("utf-8")) != _bounded(current.decode("utf-8")):
                modified_outside_block = True
            if current != proposed:
                needs_refresh = True
    except (ProposalError, OSError, UnicodeError):
        return "existing_pr_attention"
    latest = _json_command(command, "gh", "api", f"repos/{repository}/pulls/{number}")
    if not isinstance(latest, dict) or not isinstance(latest.get("head"), dict):
        return "existing_pr_attention"
    if latest.get("state") != "open" or latest["head"].get("sha") != head_sha:
        return "existing_pr_attention"
    if not verify_main(command, sha):
        return "main_advanced"
    if modified_outside_block:
        return "existing_pr_modified"
    return "existing_pr_stale" if needs_refresh else "existing_pr_current"


def propose(
    command: Commands, *,
    preview_dir: Path,
    repository: str,
    sha: str,
    run_id: str,
    run_attempt: str,
    event: str,
    ref: str,
    publish: str,
) -> tuple[str, str | None]:
    """Propose an update through an exclusively new branch and a reviewable PR.

    Returns a state and optional branch name. Any failed write raises an error
    rather than claiming that a PR was created.
    """
    if not eligible(event, ref, publish):
        return "skipped_not_authorized", None
    if not REPO_PATTERN.fullmatch(repository) or not SHA_PATTERN.fullmatch(sha):
        raise ProposalError("Invalid repository or rendered commit identifier")
    if not RUN_PATTERN.fullmatch(run_id) or int(run_id) < 1:
        raise ProposalError("Invalid workflow run identifier")
    if not RUN_PATTERN.fullmatch(run_attempt) or int(run_attempt) < 1:
        raise ProposalError("Invalid workflow run attempt")
    head = required(command, "git", "rev-parse", "HEAD")
    if head != sha:
        raise ProposalError("Publication checkout does not match the rendered commit")
    pending = existing_proposal(command, repository)
    changed = changed_preview(preview_dir)
    if pending is not None:
        return inspect_existing(command, repository, pending, preview_dir, sha), str(pending["number"])
    if not changed:
        return "unchanged", None
    if not verify_main(command, sha):
        return "main_advanced", None

    # GitHub re-runs retain GITHUB_RUN_ID but increment GITHUB_RUN_ATTEMPT.
    # A new branch avoids non-fast-forward pushes to a branch left by a failed PR creation.
    branch = f"automation/external-contributions-{run_id}-{run_attempt}"
    required(command, "git", "switch", "-c", branch)
    for filename, contents in changed.items():
        Path(filename).write_bytes(contents)
    required(command, "git", "add", "--", "README.md", "README.en.md")
    staged = command.run("git", "diff", "--cached", "--quiet", "--", "README.md", "README.en.md")
    if staged.returncode == 0:
        return "unchanged", None
    if staged.returncode != 1:
        raise ProposalError("Could not verify the proposed staged README changes")
    required(
        command, "git",
        "-c", "user.name=github-actions[bot]",
        "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", "docs: refresh curated external contributions",
    )
    if not verify_main(command, sha):
        return "main_advanced", None
    required(command, "git", "push", "origin", f"HEAD:refs/heads/{branch}")
    if not verify_main(command, sha):
        # The proposed branch may remain remotely; avoid opening a stale PR.
        return "main_advanced", branch
    created = command.run(
        "gh", "pr", "create", "--repo", repository, "--base", "main",
        "--head", branch,
        "--title", "docs: atualizar contribuições open source externas",
        "--body", (
            "Atualização automática proposta para revisão humana. Modifica somente "
            "os blocos delimitados em README.md e README.en.md. "
            f"Origem: workflow run {run_id}, tentativa {run_attempt}. "
            "Verifique os estados dos PRs, links e checks obrigatórios antes de integrar."
        ),
    )
    if created.returncode != 0:
        raise ProposalError(
            f"PR creation denied for {branch}. Review the preview artifact and "
            "create a PR manually from the already pushed branch."
        )
    for workflow in WORKFLOWS:
        result = command.run("gh", "workflow", "run", workflow, "--repo", repository, "--ref", branch)
        if result.returncode != 0:
            return "checks_unavailable", branch
    return "created", branch


def main(argv: list[str] | None = None, command: Commands | None = None) -> int:
    """Run the production script and emit a concise Actions summary."""
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
        state, branch = propose(
            command or Commands(), preview_dir=args.preview_dir,
            repository=args.repo, sha=args.sha, run_id=args.run_id,
            run_attempt=args.run_attempt,
            event=args.event, ref=args.ref, publish=args.publish,
        )
    except (ProposalError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Update proposal failed: {error}", file=sys.stderr)
        return 1
    messages = {
        "skipped_not_authorized": "Publication denied outside eligible main runs.",
        "existing_pr_current": "The open update PR already matches the latest verified preview. No new PR was created.",
        "existing_pr_stale": "The open update PR differs from the latest verified preview. Review and close the stale PR, then rerun the workflow on current main with publish=true to propose a replacement. The existing branch and reviews were preserved.",
        "existing_pr_modified": "The open update PR also changes text outside the managed README blocks. Review and preserve any human edits before manually closing and requesting a replacement; no files or reviews were changed.",
        "existing_pr_attention": "The existing update PR changed, disappeared, or could not be inspected safely. Review the PR and its branch manually before rerunning the workflow; no replacement was created.",
        "unchanged": "No README changes; branch and PR not created.",
        "main_advanced": "main advanced during this run. Rerun from the latest main commit.",
        "checks_unavailable": "Update PR created, but at least one required check was not dispatched. Run checks manually before merging.",
        "created": "A new README update PR was created for human review. main remains unchanged.",
    }
    message = messages[state]
    print(message)
    is_existing = state.startswith("existing_pr_")
    if branch:
        print(f"Existing PR: https://github.com/{args.repo}/pull/{branch}" if is_existing else f"Proposed branch: {branch}")
    if state in ("existing_pr_stale", "existing_pr_modified", "existing_pr_attention"):
        print(f"::warning::{message}", file=sys.stderr)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(message + "\n")
            if branch:
                summary.write(f"Existing PR: https://github.com/{args.repo}/pull/{branch}\n" if is_existing else f"Branch: {branch}\n")
    if state == "checks_unavailable":
        print("::warning::One or more required check workflows were not dispatched.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
