"""Offline tests for the real production PR publication code, without GitHub writes."""

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
BRANCH = "automation/external-contributions-12345"
BEGIN = "<!-- EXTERNAL_CONTRIBUTIONS:START -->"
END = "<!-- EXTERNAL_CONTRIBUTIONS:END -->"


class FakeCommands:
    """Emulate git/gh responses, recording every attempted external action."""

    def __init__(self, *, existing=False, remote_shas=None, failure=None, dispatch_failure=None):
        self.commands = []
        self.existing = existing
        self.remote_shas = list(remote_shas if remote_shas is not None else [SHA] * 4)
        self.failure = failure
        self.dispatch_failure = dispatch_failure

    def run(self, *args):
        self.commands.append(args)
        if self.failure and args[:len(self.failure)] == self.failure:
            return subprocess.CompletedProcess(args, 1, "", "sensitive failure output")
        if args[:3] == ("git", "rev-parse", "HEAD"):
            return subprocess.CompletedProcess(args, 0, SHA + "\n", "")
        if args[:3] == ("gh", "pr", "list"):
            prs = [{"headRefName": BRANCH}] if self.existing else []
            return subprocess.CompletedProcess(args, 0, json.dumps(prs), "")
        if args[:2] == ("git", "ls-remote"):
            sha = self.remote_shas.pop(0) if self.remote_shas else SHA
            return subprocess.CompletedProcess(args, 0, sha + "\trefs/heads/main\n", "")
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
            run_id="12345", event="schedule", ref="refs/heads/main", publish="false",
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
        self.assertEqual(self.call(fake), ("existing_pr", None))
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

    def test_cli_denies_pull_request_event_without_running_any_command(self):
        fake = FakeCommands()
        result = main([
            "--preview-dir", str(self.preview), "--repo", REPO, "--sha", SHA,
            "--run-id", "12345", "--event", "pull_request",
            "--ref", "refs/heads/main", "--publish", "true",
        ], command=fake)
        self.assertEqual(result, 0)
        self.assertEqual(fake.commands, [])


if __name__ == "__main__":
    unittest.main()
