#!/usr/bin/env python3
"""Propose a reviewed README-only update; never write to the protected main branch.

The GitHub Actions job gates publication independently. This module repeats
that eligibility check so the exact publication logic can be unit tested.
"""

from __future__ import annotations

import argparse
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


def open_automation_prs(command: Commands, repository: str) -> bool:
    """Fail closed if the GitHub CLI cannot enumerate all open proposals."""
    response = required(
        command, "gh", "pr", "list", "--repo", repository, "--base", "main",
        "--state", "open", "--limit", "100", "--json", "headRefName",
    )
    try:
        prs = json.loads(response)
    except ValueError as error:
        raise ProposalError("GitHub returned invalid pull request data") from error
    if not isinstance(prs, list) or len(prs) >= 100:
        raise ProposalError("Cannot reliably inspect all open update pull requests")
    return any(
        isinstance(pr, dict)
        and isinstance(pr.get("headRefName"), str)
        and pr["headRefName"].startswith("automation/external-contributions-")
        for pr in prs
    )


def propose(
    command: Commands, *,
    preview_dir: Path,
    repository: str,
    sha: str,
    run_id: str,
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
    if not RUN_PATTERN.fullmatch(run_id):
        raise ProposalError("Invalid workflow run identifier")
    head = required(command, "git", "rev-parse", "HEAD")
    if head != sha:
        raise ProposalError("Publication checkout does not match the rendered commit")
    if open_automation_prs(command, repository):
        return "existing_pr", None
    changed = changed_preview(preview_dir)
    if not changed:
        return "unchanged", None
    if not verify_main(command, sha):
        return "main_advanced", None

    branch = f"automation/external-contributions-{run_id}"
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
            f"Origem: workflow run {run_id}. "
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
    parser.add_argument("--event", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--publish", default="false")
    args = parser.parse_args(argv)
    try:
        state, branch = propose(
            command or Commands(), preview_dir=args.preview_dir,
            repository=args.repo, sha=args.sha, run_id=args.run_id,
            event=args.event, ref=args.ref, publish=args.publish,
        )
    except (ProposalError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Update proposal failed: {error}", file=sys.stderr)
        return 1
    messages = {
        "skipped_not_authorized": "Publication denied outside eligible main runs.",
        "existing_pr": "An automatic update PR is open. Review it before another proposal.",
        "unchanged": "No README changes; branch and PR not created.",
        "main_advanced": "main advanced during this run. Rerun from the latest main commit.",
        "checks_unavailable": "Update PR created, but at least one required check was not dispatched. Run checks manually before merging.",
        "created": "A new README update PR was created for human review. main remains unchanged.",
    }
    message = messages[state]
    print(message)
    if branch:
        print(f"Proposed branch: {branch}")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(message + "\n")
            if branch:
                summary.write(f"Branch: {branch}\n")
    if state == "checks_unavailable":
        print("::warning::One or more required check workflows were not dispatched.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
