"""Offline tests for the real production PR publication code, without GitHub writes."""

import base64
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.propose_external_contributions import ProposalError, eligible, main, propose


SHA = "a" * 40
NEW_SHA = "b" * 40
REPO = "example/profile"
BRANCH = "automation/external-contributions-12345-1"
BEGIN = "<!-- EXTERNAL_CONTRIBUTIONS:START -->"
END = "<!-- EXTERNAL_CONTRIBUTIONS:END -->"


class FakeCommands:
    """Emulate git/gh responses, recording every attempted external action."""

    def __init__(self, *, existing=False, remote_shas=None, failure=None, dispatch_failure=None,
                 remote_branches=None, head_files=None, pr_states=None, head_shas=None,
                 fork=False, removed_branch=False):
        self.commands = []
        self.existing = existing
        self.remote_shas = list(remote_shas if remote_shas is not None else [SHA] * 4)
        self.failure = failure
        self.dispatch_failure = dispatch_failure
        self.remote_branches = remote_branches if remote_branches is not None else set()
        self.head_files = head_files
        self.pr_states = list(pr_states or ["open"])
        self.head_shas = list(head_shas or ["c" * 40])
        self.fork = fork
        self.removed_branch = removed_branch

    def run(self, *args):
        self.commands.append(args)
        if self.failure and args[:len(self.failure)] == self.failure:
            return subprocess.CompletedProcess(args, 1, "", "sensitive failure output")
        if args[:3] == ("git", "rev-parse", "HEAD"):
            return subprocess.CompletedProcess(args, 0, SHA + "\n", "")
        if args[:3] == ("gh", "pr", "list"):
            prs = [{"headRefName": BRANCH, "number": 44}] if self.existing else []
            return subprocess.CompletedProcess(args, 0, json.dumps(prs), "")
        if args[:2] == ("gh", "api"):
            endpoint = args[2]
            if endpoint == f"repos/{REPO}/pulls/44":
                state = self.pr_states.pop(0) if len(self.pr_states) > 1 else self.pr_states[0]
                oid = self.head_shas.pop(0) if len(self.head_shas) > 1 else self.head_shas[0]
                owner = "another-owner/example" if self.fork else REPO
                obj = {
                    "number": 44, "state": state,
                    "head": {"ref": BRANCH, "sha": oid, "repo": {"full_name": owner}},
                    "base": {"ref": "main"},
                }
                return subprocess.CompletedProcess(args, 0, json.dumps(obj), "")
            if "/contents/" in endpoint:
                if self.removed_branch:
                    return subprocess.CompletedProcess(args, 1, "", "404 Not Found")
                filename = endpoint.split("/contents/", 1)[1].split("?ref=", 1)[0]
                raw = (self.head_files or {}).get(filename)
                if raw is None:
                    raw = (Path("preview") / filename).read_bytes()
                obj = {"encoding": "base64", "content": base64.b64encode(raw).decode()}
                return subprocess.CompletedProcess(args, 0, json.dumps(obj), "")
            raise AssertionError(f"Unexpected gh api request: {endpoint}")
        if args[:2] == ("git", "ls-remote"):
            sha = self.remote_shas.pop(0) if self.remote_shas else SHA
            return subprocess.CompletedProcess(args, 0, sha + "\trefs/heads/main\n", "")
        if args[:2] == ("git", "push"):
            remote_ref = args[-1]
            if remote_ref in self.remote_branches:
                return subprocess.CompletedProcess(args, 1, "", "non-fast-forward")
            self.remote_branches.add(remote_ref)
        if args[:3] == ("git", "diff", "--cached"):
            return subprocess.CompletedProcess(args, 1, "", "")
        if args[:3] == ("gh", "workflow", "run") and args[3] == self.dispatch_failure:
            return subprocess.CompletedProcess(args, 1, "", "permission denied")
        return subprocess.CompletedProcess(args, 0, "", "")

    def actions(self, *prefix):
        return [args for args in self.commands if args[:len(prefix)] == prefix]


class ProposalTests(unittest.TestCase):
    """Exercise authorization, concurrency and the actual PR creation path."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.old_cwd = Path.cwd()
        os.chdir(self.folder.name)
        self.addCleanup(os.chdir, self.old_cwd)
        self.preview = Path(self.folder.name) / "preview"
        self.preview.mkdir()
        for language in ("README.md", "README.en.md"):
            original = "# Profile\n\n" + BEGIN + "\n\nOld values\n\n" + END + "\n\nFooter\n"
            proposed = original.replace("Old values", "New verified values")
            Path(language).write_text(original, encoding="utf-8")
            (self.preview / language).write_text(proposed, encoding="utf-8")

    def call(self, cmd, **overrides):
        params = dict(
            preview_dir=self.preview, repository=REPO, sha=SHA,
            run_id="12345", run_attempt="1", event="schedule", ref="refs/heads/main", publish="false",
        )
        params.update(overrides)
        return propose(cmd, **params)

    def test_only_main_schedule_and_explicit_main_dispatch_can_publish(self):
        self.assertTrue(eligible("schedule", "refs/heads/main", "false"))
        self.assertTrue(eligible("workflow_dispatch", "refs/heads/main", "true"))
        for event, ref, publish in (
            ("push", "refs/heads/main", "true"),
            ("pull_request", "refs/heads/main", "true"),
            ("schedule", "refs/heads/feature", "true"),
            ("workflow_dispatch", "refs/heads/main", "false"),
            ("workflow_dispatch", "refs/heads/feature", "true"),
        ):
            with self.subTest(event=event, ref=ref):
                self.assertFalse(eligible(event, ref, publish))
                fake = FakeCommands()
                self.assertEqual(
                    self.call(fake, event=event, ref=ref, publish=publish),
                    ("skipped_not_authorized", None),
                )
                self.assertEqual(fake.commands, [])

    def test_no_change_does_not_make_branch_or_pr(self):
        for name in ("README.md", "README.en.md"):
            (self.preview / name).write_bytes(Path(name).read_bytes())
        fake = FakeCommands()
        self.assertEqual(self.call(fake), ("unchanged", None))
        self.assertEqual(fake.actions("git", "switch"), [])
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_existing_update_pr_stops_before_modifying_files(self):
        fake = FakeCommands(existing=True)
        old = Path("README.md").read_bytes()
        self.assertEqual(self.call(fake), ("existing_pr_current", "44"))
        self.assertEqual(Path("README.md").read_bytes(), old)
        self.assertEqual(fake.actions("git", "switch"), [])

    def test_success_creates_branch_and_pr_and_dispatches_both_checks(self):
        fake = FakeCommands()
        state, branch = self.call(fake)
        self.assertEqual((state, branch), ("created", BRANCH))
        self.assertIn("New verified values", Path("README.md").read_text(encoding="utf-8"))
        self.assertEqual(fake.actions("git", "switch"), [("git", "switch", "-c", BRANCH)])
        self.assertEqual(fake.actions("git", "push"), [
            ("git", "push", "origin", f"HEAD:refs/heads/{BRANCH}"),
        ])
        self.assertEqual(len(fake.actions("gh", "pr", "create")), 1)
        self.assertEqual(
            [cmd[3] for cmd in fake.actions("gh", "workflow", "run")],
            ["validate-profile.yml", "spell-check.yml"],
        )
        self.assertEqual(fake.actions("git", "push", "origin", "HEAD:refs/heads/main"), [])

    def test_existing_pr_with_outdated_preview_requests_manual_replacement(self):
        fake = FakeCommands(
            existing=True,
            head_files={name: Path(name).read_bytes()
                        for name in ("README.md", "README.en.md")},
        )
        self.assertEqual(self.call(fake), ("existing_pr_stale", "44"))
        self.assertEqual(fake.actions("git", "push"), [])
        self.assertEqual(fake.actions("gh", "pr", "create"), [])
        self.assertEqual(fake.actions("gh", "pr", "comment"), [])
        self.assertEqual(fake.actions("gh", "pr", "close"), [])

    def test_existing_pr_with_human_editorial_change_is_preserved(self):
        head_files = {}
        for name in ("README.md", "README.en.md"):
            head_files[name] = (self.preview / name).read_bytes().replace(
                b"Editorial footer", b"Human editorial change",
            )
        fake = FakeCommands(existing=True, head_files=head_files)
        self.assertEqual(self.call(fake), ("existing_pr_modified", "44"))
        self.assertEqual(fake.actions("git", "switch"), [])
        self.assertEqual(fake.actions("git", "push"), [])
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_existing_branch_missing_requires_manual_attention(self):
        fake = FakeCommands(existing=True, removed_branch=True)
        self.assertEqual(self.call(fake), ("existing_pr_attention", "44"))
        self.assertEqual(fake.actions("git", "push"), [])
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_pr_closed_during_inspection_requires_manual_attention(self):
        fake = FakeCommands(existing=True, pr_states=["open", "closed"])
        self.assertEqual(self.call(fake), ("existing_pr_attention", "44"))
        self.assertEqual(fake.actions("git", "push"), [])
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_concurrent_pr_head_change_requires_manual_attention(self):
        fake = FakeCommands(existing=True, head_shas=["c" * 40, "d" * 40])
        self.assertEqual(self.call(fake), ("existing_pr_attention", "44"))
        self.assertEqual(fake.actions("git", "push"), [])
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_similarly_named_fork_pr_does_not_block_own_proposal(self):
        fake = FakeCommands(existing=True, fork=True)
        self.assertEqual(self.call(fake), ("created", BRANCH))
        self.assertEqual(len(fake.actions("gh", "pr", "create")), 1)

    def test_existing_pr_with_main_advanced_does_not_read_or_modify_it(self):
        fake = FakeCommands(existing=True, remote_shas=[NEW_SHA])
        self.assertEqual(self.call(fake), ("main_advanced", "44"))
        self.assertEqual(fake.actions("gh", "pr", "create"), [])
        self.assertEqual(fake.actions("git", "push"), [])

    def test_two_runs_on_same_open_pr_never_duplicate_or_mutate(self):
        for _ in range(2):
            fake = FakeCommands(existing=True)
            self.assertEqual(self.call(fake), ("existing_pr_current", "44"))
            self.assertEqual(fake.actions("git", "push"), [])
            self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_main_summary_identifies_existing_pr_to_review(self):
        fake = FakeCommands(existing=True, head_files={
            name: Path(name).read_bytes() for name in ("README.md", "README.en.md")
        })
        summary = self.preview / "summary.md"
        with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary)}):
            code = main([
                "--preview-dir", str(self.preview), "--repo", REPO, "--sha", SHA,
                "--run-id", "12345", "--run-attempt", "1", "--event", "schedule",
                "--ref", "refs/heads/main",
            ], command=fake)
        self.assertEqual(code, 0)
        text = summary.read_text(encoding="utf-8")
        self.assertIn("https://github.com/example/profile/pull/44", text)
        self.assertIn("Review and close the stale PR", text)
        self.assertEqual(fake.actions("git", "push"), [])

    def test_private_or_unexpected_markdown_outside_markers_is_rejected(self):
        for name in ("README.md", "README.en.md"):
            original = (self.preview / name).read_text(encoding="utf-8")
            for altered in (
                original.replace("Footer", "Footer modified"),
                original.replace(BEGIN, ""),
                original.replace(END, ""),
            ):
                with self.subTest(name=name, altered=altered[-35:]):
                    (self.preview / name).write_text(altered, encoding="utf-8")
                    fake = FakeCommands()
                    with self.assertRaises(ProposalError):
                        self.call(fake)
                    self.assertEqual(fake.actions("git", "switch"), [])
            (self.preview / name).write_text(original, encoding="utf-8")

    def test_main_advanced_before_branch_creation_prevents_all_writes(self):
        fake = FakeCommands(remote_shas=[NEW_SHA])
        old = Path("README.md").read_bytes()
        self.assertEqual(self.call(fake), ("main_advanced", None))
        self.assertEqual(fake.actions("git", "switch"), [])
        self.assertEqual(Path("README.md").read_bytes(), old)

    def test_main_advanced_before_push_does_not_push(self):
        fake = FakeCommands(remote_shas=[SHA, NEW_SHA])
        self.assertEqual(self.call(fake), ("main_advanced", None))
        self.assertEqual(fake.actions("git", "push"), [])
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_main_advanced_after_push_does_not_open_stale_pr(self):
        fake = FakeCommands(remote_shas=[SHA, SHA, NEW_SHA])
        self.assertEqual(self.call(fake), ("main_advanced", BRANCH))
        self.assertEqual(len(fake.actions("git", "push")), 1)
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_failed_push_is_an_error_and_never_creates_pr(self):
        fake = FakeCommands(failure=("git", "push"))
        with self.assertRaisesRegex(ProposalError, "git push") as caught:
            self.call(fake)
        self.assertNotIn("sensitive failure output", str(caught.exception))
        self.assertEqual(fake.actions("gh", "pr", "create"), [])

    def test_failed_pr_creation_does_not_claim_success_or_dispatch_checks(self):
        fake = FakeCommands(failure=("gh", "pr", "create"))
        with self.assertRaisesRegex(ProposalError, "PR creation denied"):
            self.call(fake)
        self.assertEqual(fake.actions("gh", "workflow", "run"), [])

    def test_missing_permissions_to_enumerate_existing_prs_prevents_any_write(self):
        fake = FakeCommands(failure=("gh", "pr", "list"))
        with self.assertRaisesRegex(ProposalError, "gh pr"):
            self.call(fake)
        self.assertEqual(fake.actions("git", "switch"), [])

    def test_check_dispatch_failure_is_reported_and_does_not_merge(self):
        fake = FakeCommands(dispatch_failure="spell-check.yml")
        self.assertEqual(self.call(fake), ("checks_unavailable", BRANCH))
        self.assertEqual(fake.actions("gh", "pr", "merge"), [])

    def test_commit_sha_mismatch_refuses_publication(self):
        fake = FakeCommands()
        with self.assertRaisesRegex(ProposalError, "rendered commit"):
            self.call(fake, sha=NEW_SHA)
        self.assertEqual(fake.actions("git", "switch"), [])

    def test_retry_after_pr_creation_denied_uses_new_branch_and_succeeds(self):
        """A re-run must not collide with an already pushed branch from attempt 1."""
        shared_remote = set()
        first = FakeCommands(
            failure=("gh", "pr", "create"),
            remote_branches=shared_remote,
        )
        with self.assertRaisesRegex(ProposalError, "PR creation denied"):
            self.call(first, run_attempt="1")
        self.assertIn(f"HEAD:refs/heads/{BRANCH}", shared_remote)

        # A new GitHub attempt starts from the unchanged main checkout and
        # uses a fresh local working tree with an identical, still-valid preview.
        for filename in ("README.md", "README.en.md"):
            Path(filename).write_text(
                "# Profile\n\n" + BEGIN + "\n\nOld values\n\n" + END + "\n\nFooter\n",
                encoding="utf-8",
            )
        second = FakeCommands(remote_branches=shared_remote)
        state, branch = self.call(second, run_attempt="2")
        self.assertEqual(state, "created")
        self.assertEqual(branch, "automation/external-contributions-12345-2")
        self.assertEqual(len(shared_remote), 2)
        self.assertEqual(second.actions("git", "push"), [
            ("git", "push", "origin", f"HEAD:refs/heads/{branch}"),
        ])
        self.assertEqual(len(second.actions("gh", "pr", "create")), 1)

    def test_retry_after_main_advanced_post_push_uses_fresh_branch(self):
        shared_remote = set()
        first = FakeCommands(remote_shas=[SHA, SHA, NEW_SHA], remote_branches=shared_remote)
        self.assertEqual(self.call(first, run_attempt="1"), ("main_advanced", BRANCH))
        for filename in ("README.md", "README.en.md"):
            Path(filename).write_text(
                "# Profile\n\n" + BEGIN + "\n\nOld values\n\n" + END + "\n\nFooter\n",
                encoding="utf-8",
            )
        second = FakeCommands(remote_branches=shared_remote)
        self.assertEqual(
            self.call(second, run_attempt="2"),
            ("created", "automation/external-contributions-12345-2"),
        )

    def test_invalid_run_attempt_fails_before_any_git_or_github_operation(self):
        for attempt in ("", "0", "-1", "1-invalid", "abc"):
            with self.subTest(attempt=attempt):
                fake = FakeCommands()
                with self.assertRaisesRegex(ProposalError, "run attempt"):
                    self.call(fake, run_attempt=attempt)
                self.assertEqual(fake.commands, [])

    def test_cli_requires_run_attempt_for_eligible_publication(self):
        fake = FakeCommands()
        with self.assertRaises(SystemExit) as raised:
            main([
                "--preview-dir", str(self.preview), "--repo", REPO, "--sha", SHA,
                "--run-id", "12345", "--event", "schedule",
                "--ref", "refs/heads/main",
            ], command=fake)
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(fake.commands, [])

    def test_cli_denies_pull_request_event_without_running_any_command(self):
        fake = FakeCommands()
        result = main([
            "--preview-dir", str(self.preview), "--repo", REPO, "--sha", SHA,
            "--run-id", "12345", "--run-attempt", "1", "--event", "pull_request",
            "--ref", "refs/heads/main", "--publish", "true",
        ], command=fake)
        self.assertEqual(result, 0)
        self.assertEqual(fake.commands, [])


if __name__ == "__main__":
    unittest.main()
