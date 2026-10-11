import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.propose_external_contributions import (
    BOT_EMAIL, BOT_NAME, BRANCH, ProposalError, _ensure_managed_branch_absent,
    _same_catalog_facts, _verify_existing_head, eligible, existing_proposal, propose,
)

MAIN_SHA = "a" * 40
HEAD_SHA = "b" * 40
REPO = "rodri-oliveira-dev/rodri-oliveira-dev"


class FakeCommands:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def run(self, *args):
        self.calls.append(args)
        value = self.handler(args)
        if isinstance(value, tuple):
            code, output = value
        else:
            code, output = 0, value
        return subprocess.CompletedProcess(args, code, output or "", "")


def trusted_pr():
    return {"number": 44, "author": {"login": "github-actions[bot]"},
            "headRefName": BRANCH, "headRefOid": HEAD_SHA,
            "headRepository": {"nameWithOwner": REPO}, "isCrossRepository": False}


class ProposalTests(unittest.TestCase):
    def test_only_explicit_main_runs_are_eligible(self):
        self.assertTrue(eligible("schedule", "refs/heads/main", "false"))
        self.assertTrue(eligible("workflow_dispatch", "refs/heads/main", "true"))
        self.assertFalse(eligible("pull_request", "refs/heads/main", "true"))
        self.assertFalse(eligible("workflow_dispatch", "refs/heads/main", "false"))

    def test_existing_proposal_must_be_bot_owned_and_not_a_fork(self):
        fake = FakeCommands(lambda _args: json.dumps([trusted_pr()]))
        self.assertEqual(existing_proposal(fake, REPO)["number"], 44)
        self.assertIn("--head", fake.calls[0])
        self.assertEqual(fake.calls[0][fake.calls[0].index("--head") + 1], BRANCH)
        self.assertIn("--limit", fake.calls[0])
        bad = trusted_pr()
        bad["isCrossRepository"] = True
        with self.assertRaisesRegex(ProposalError, "untrusted"):
            existing_proposal(FakeCommands(lambda _args: json.dumps([bad])), REPO)

    def test_manual_unexpected_files_block_update(self):
        def handler(args):
            if args[:2] == ("gh", "api"):
                return json.dumps({"state": "open", "head": {"sha": HEAD_SHA}})
            if args[:3] == ("gh", "pr", "diff"):
                return "docs/open-source-contributions.md\nREADME.md\n"
            raise AssertionError(args)
        with self.assertRaisesRegex(ProposalError, "unexpected manual"):
            _verify_existing_head(FakeCommands(handler), REPO,
                                  {"number": 44, "sha": HEAD_SHA, "branch": BRANCH})

    def test_existing_trusted_pr_is_updated_by_fast_forward_without_force(self):
        def handler(args):
            if args == ("git", "rev-parse", "HEAD"):
                return MAIN_SHA
            if args == ("git", "rev-parse", "FETCH_HEAD"):
                return HEAD_SHA
            if args[:3] == ("git", "fetch", "--no-tags") or args[:2] == ("git", "switch"):
                return ""
            if args[:2] == ("git", "push"):
                return ""
            raise AssertionError(args)
        fake = FakeCommands(handler)
        with tempfile.TemporaryDirectory() as directory, \
             patch("scripts.propose_external_contributions.changed_preview", return_value={"changed": b"x"}), \
             patch("scripts.propose_external_contributions.existing_proposal", return_value={"number": 44, "sha": HEAD_SHA, "branch": BRANCH}), \
             patch("scripts.propose_external_contributions.verify_main", return_value=True), \
             patch("scripts.propose_external_contributions._verify_existing_head"), \
             patch("scripts.propose_external_contributions.verified_preview", return_value={"managed": b"data"}), \
             patch("scripts.propose_external_contributions._preview_matches_current_catalog", return_value=False), \
             patch("scripts.propose_external_contributions._apply_and_commit", return_value=True), \
             patch("scripts.propose_external_contributions._dispatch_checks", return_value=True):
            state = propose(fake, preview_dir=Path(directory), repository=REPO, sha=MAIN_SHA,
                            run_id="1", run_attempt="1", event="schedule",
                            ref="refs/heads/main", publish="false")
        self.assertEqual(state, ("updated", "44"))
        flat = " ".join(" ".join(call) for call in fake.calls)
        self.assertIn(f"HEAD:refs/heads/{BRANCH}", flat)
        self.assertNotIn("--force", flat)
        self.assertNotIn("pr create", flat)

    def test_existing_pr_ignores_timestamp_only_preview_change(self):
        def handler(args):
            if args == ("git", "rev-parse", "HEAD"):
                return MAIN_SHA
            if args == ("git", "rev-parse", "FETCH_HEAD"):
                return HEAD_SHA
            if args[:3] == ("git", "fetch", "--no-tags") or args[:2] == ("git", "switch"):
                return ""
            raise AssertionError(args)
        fake = FakeCommands(handler)
        with tempfile.TemporaryDirectory() as directory, \
             patch("scripts.propose_external_contributions.changed_preview", return_value={"changed": b"x"}), \
             patch("scripts.propose_external_contributions.existing_proposal", return_value={"number": 44, "sha": HEAD_SHA, "branch": BRANCH}), \
             patch("scripts.propose_external_contributions.verify_main", return_value=True), \
             patch("scripts.propose_external_contributions._verify_existing_head"), \
             patch("scripts.propose_external_contributions.verified_preview", return_value={"managed": b"data"}), \
             patch("scripts.propose_external_contributions._preview_matches_current_catalog", return_value=True), \
             patch("scripts.propose_external_contributions._apply_and_commit") as apply_commit:
            state = propose(fake, preview_dir=Path(directory), repository=REPO, sha=MAIN_SHA,
                            run_id="1", run_attempt="1", event="schedule",
                            ref="refs/heads/main", publish="false")
        self.assertEqual(state, ("existing_pr_current", "44"))
        apply_commit.assert_not_called()

    def test_catalog_fact_comparison_ignores_only_sync_timestamp(self):
        first = {"last_successful_sync": "2026-10-11T00:00:00Z", "totals": {"open": 1}}
        later = {"last_successful_sync": "2026-10-12T00:00:00Z", "totals": {"open": 1}}
        changed = {"last_successful_sync": "2026-10-12T00:00:00Z", "totals": {"open": 0}}
        self.assertTrue(_same_catalog_facts(first, later))
        self.assertFalse(_same_catalog_facts(first, changed))

    def test_managed_remote_branch_must_be_absent_before_creation(self):
        with self.assertRaisesRegex(ProposalError, "exists without an open PR"):
            _ensure_managed_branch_absent(FakeCommands(lambda _args: (0, HEAD_SHA)))
        with self.assertRaisesRegex(ProposalError, "Could not inspect"):
            _ensure_managed_branch_absent(FakeCommands(lambda _args: (1, "")))
        _ensure_managed_branch_absent(FakeCommands(lambda _args: (2, "")))

    def test_bot_commit_identity_is_verified(self):
        def handler(args):
            if args[:2] == ("gh", "api") and "/pulls/" in args[2]:
                return json.dumps({"state": "open", "head": {"sha": HEAD_SHA}})
            if args[:3] == ("gh", "pr", "diff"):
                return "docs/open-source-contributions.md\n"
            if args[:2] == ("gh", "api"):
                identity = {"name": BOT_NAME, "email": BOT_EMAIL}
                return json.dumps({"author": identity, "committer": identity})
            raise AssertionError(args)
        _verify_existing_head(FakeCommands(handler), REPO,
                              {"number": 44, "sha": HEAD_SHA, "branch": BRANCH})


if __name__ == "__main__":
    unittest.main()
