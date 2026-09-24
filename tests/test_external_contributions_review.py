"""Review-history contract tests without GitHub access or repository writes."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.discover_external_contributions import discover
from scripts.external_contributions import CollectionError
from scripts.external_contributions_review import classify_candidates, load_review_registry
from test_discover_external_contributions import FakeAPI, config, issue, response


DATE = "2026-09-24"
LOGIN = "rodri-oliveira-dev"
KNOWN = "NewOrg/KnownProject"
NEW = "AnotherOrg/NewProject"
CURATED = "SomeOrg/Curated"


def review_entry(repository=KNOWN, status="pending", observed=None, **extra):
    return {
        "repository": repository, "status": status, "observed_at": DATE,
        "observed_prs": {"7": "open"} if observed is None else observed, **extra,
    }


def registry(*projects):
    return {"schema_version": 1, "profile": LOGIN, "projects": list(projects)}


def run(items, review):
    return discover(
        config(), FakeAPI({1: response(items)}), registry=review,
    )


class ReviewRegistryTests(unittest.TestCase):
    def load(self, data, settings=None):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "review.json"
            file.write_text(json.dumps(data), encoding="utf-8")
            return load_review_registry(file, settings or config())

    def test_versioned_pending_is_valid_but_not_approved(self):
        data = registry(review_entry())
        self.assertEqual(self.load(data), data)
        report = run([issue(KNOWN, 7)], data)
        review = report["review"]
        self.assertEqual(review["untracked_count"], 0)
        self.assertEqual(review["changed_count"], 0)
        self.assertEqual(review["known_pending_repositories"], [KNOWN])
        self.assertEqual([x["repository"] for x in report["candidate_repositories"]], [KNOWN])
        self.assertNotIn(KNOWN, {p["repository"] for p in config()["projects"]})

    def test_unseen_repository_is_reported_separately(self):
        report = run([issue(KNOWN, 7), issue(NEW, 3)], registry(review_entry()))
        self.assertEqual([x["repository"] for x in report["review"]["new_candidates"]], [NEW])
        self.assertEqual(report["review"]["untracked_count"], 1)
        self.assertEqual(report["review"]["known_pending_repositories"], [KNOWN])

    def test_new_pr_and_status_transition_are_relevant_changes(self):
        report = run(
            [issue(KNOWN, 7, "closed", "2026-09-24T10:00:00Z"), issue(KNOWN, 8)],
            registry(review_entry()),
        )
        changes = report["review"]["changed_candidates"]
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["new_pr_numbers"], [8])
        self.assertEqual(changes[0]["updated_pr_numbers"], [7])
        self.assertEqual(changes[0]["missing_pr_numbers"], [])

    def test_absent_pr_is_flagged_not_assumed_deleted(self):
        result = run([issue(KNOWN, 8)], registry(review_entry()))
        self.assertEqual(result["review"]["changed_candidates"][0]["missing_pr_numbers"], [7])

    def test_ignored_repository_keeps_history_without_daily_alert(self):
        result = run(
            [issue(KNOWN, 7, "closed", "2026-09-24T10:00:00Z"), issue(KNOWN, 8)],
            registry(review_entry(status="ignored", decision_date=DATE, reason="Not relevant")),
        )
        self.assertEqual(result["review"]["ignored_repositories"], [KNOWN])
        self.assertEqual(result["review"]["changed_count"], 0)
        self.assertEqual(result["review"]["untracked_count"], 0)
        self.assertEqual(len(result["candidate_repositories"]), 1)

    def test_selected_project_is_excluded_from_candidates(self):
        entry = review_entry(repository=CURATED, status="selected", observed={}, decision_date=DATE)
        result = run([issue(CURATED, 1)], registry(entry))
        self.assertEqual(result["candidate_repositories"], [])
        self.assertEqual(result["review"]["untracked_count"], 0)

    def test_case_insensitive_match_and_duplicate_api_results_do_not_alert(self):
        result = run([issue("neworg/knownproject", 7)], registry(review_entry()))
        self.assertEqual(result["review"]["untracked_count"], 0)
        self.assertEqual(result["review"]["changed_count"], 0)

    def test_documented_rename_alias_keeps_history(self):
        entry = review_entry(aliases=["FormerOwner/FormerName"])
        result = run([issue("formerowner/formername", 7)], registry(entry))
        self.assertEqual(result["review"]["untracked_count"], 0)
        self.assertEqual(result["review"]["changed_count"], 0)

    def test_unrecorded_transfer_requires_review_and_does_not_rewrite_history(self):
        entry = review_entry()
        result = run([issue("TransferredOrg/KnownProject", 7)], registry(entry))
        self.assertEqual(result["review"]["untracked_count"], 1)
        self.assertEqual(result["review"]["new_candidates"][0]["repository"], "TransferredOrg/KnownProject")

    def test_selected_project_renamed_requires_curated_config_update(self):
        entry = review_entry(repository=CURATED, status="selected", observed={},
                             aliases=["TransferredOrg/Curated"], decision_date=DATE)
        result = run([issue("TransferredOrg/Curated", 1)], registry(entry))
        self.assertEqual(result["review"]["changed_count"], 1)
        self.assertEqual(result["review"]["changed_candidates"][0]["change_reason"],
                         "selected_repository_moved")

    def test_rejects_incorrect_status_conflicts_and_duplicates(self):
        bad = [
            registry(review_entry(status="unknown")),
            registry(review_entry(status="ignored")),
            registry(review_entry(status=["pending"])),
            registry(review_entry(repository=CURATED, status="selected", observed={})),
            registry(review_entry(observed={"7": ["open"]})),
            registry(review_entry(repository=CURATED, status="pending")),
            registry(review_entry(repository=KNOWN, status="selected")),
            registry(review_entry(), review_entry(repository="neworg/knownproject")),
            registry(review_entry(aliases=[KNOWN])),
            registry(review_entry(aliases=["Different/Name"]),
                     review_entry(repository="different/name")),
            registry(review_entry(observed={"01": "open"})),
            registry(review_entry(observed={"7": "unexpected"})),
            registry(review_entry(observed_at="2026-02-30")),
            registry(review_entry(repository=f"{LOGIN}/OwnRepo")),
            registry(review_entry(aliases=[f"{LOGIN}/OwnRepo"])),
            registry(review_entry(aliases=[CURATED])),
        ]
        for data in bad:
            with self.subTest(data=data):
                with self.assertRaises(CollectionError):
                    self.load(data)

    def test_registry_schema_and_missing_file_fail_closed(self):
        for invalid in ({"schema_version": 2, "profile": LOGIN, "projects": []},
                        {"schema_version": 1, "profile": "else", "projects": []},
                        {"schema_version": 1, "profile": LOGIN, "projects": {}}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(CollectionError):
                    self.load(invalid)
        with self.assertRaises(CollectionError):
            load_review_registry(Path("/missing/registry.json"), config())

    def test_no_projects_no_changes_is_valid(self):
        result = run([], registry())
        self.assertEqual(result["review"]["new_candidates"], [])
        self.assertEqual(result["review"]["changed_candidates"], [])

    def test_registry_is_read_only_and_collects_without_changing_readme(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "review.json"
            data = registry(review_entry())
            file.write_text(json.dumps(data), encoding="utf-8")
            before = file.read_bytes()
            loaded = load_review_registry(file, config())
            run([issue(KNOWN, 7), issue(NEW, 1)], loaded)
            self.assertEqual(file.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
