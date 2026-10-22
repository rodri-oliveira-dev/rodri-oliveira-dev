import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

from scripts.external_contributions import (
    CollectionError, _fetch_window, _partitioned_search, collect,
)

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
CONFIG = {"schema_version": 2, "profile": "rodri-oliveira-dev", "exclude_repositories": []}


def issue(repository="acme/widget", number=1, *, identifier=None, state="open",
          merged_at=None, title="Useful change", created="2026-01-01T10:00:00Z",
          updated="2026-01-02T10:00:00Z", author="rodri-oliveira-dev"):
    return {"id": identifier or number * 10, "number": number, "state": state,
            "title": title, "repository_url": f"https://api.github.com/repos/{repository}",
            "html_url": f"https://github.com/{repository}/pull/{number}",
            "user": {"login": author}, "created_at": created, "updated_at": updated,
            "pull_request": {"merged_at": merged_at}}


class StaticAPI:
    def __init__(self, items, *, incomplete=False, declared=None):
        self.items = items
        self.incomplete = incomplete
        self.declared = len(items) if declared is None else declared
        self.calls = []

    def get(self, path, params):
        self.calls.append((path, params))
        page = params["page"]
        start = (page - 1) * 100
        return {"total_count": self.declared, "incomplete_results": self.incomplete,
                "items": self.items[start:start + 100]}


class CollectorTests(unittest.TestCase):
    def test_discovers_new_repositories_and_prs_and_excludes_own(self):
        api = StaticAPI([issue(), issue("new/repository", 2), issue("rodri-oliveira-dev/self", 3)])
        result = collect(CONFIG, api, NOW)
        self.assertEqual(result["totals"]["repositories"], 2)
        self.assertEqual(result["totals"]["pull_requests"], 2)
        self.assertEqual({p["repository"] for p in result["projects"]}, {"acme/widget", "new/repository"})
        self.assertIn("-user:rodri-oliveira-dev", api.calls[0][1]["q"])

    def test_reconciles_merged_closed_and_reopened_states(self):
        initial = collect(CONFIG, StaticAPI([issue()]), NOW)
        merged = collect(CONFIG, StaticAPI([issue(state="closed", merged_at="2026-02-01T10:00:00Z")]), NOW, initial)
        self.assertEqual(merged["projects"][0]["pull_requests"][0]["status"], "merged")
        closed = collect(CONFIG, StaticAPI([issue(state="closed")]), NOW, initial)
        self.assertEqual(closed["projects"][0]["pull_requests"][0]["status"], "closed_unmerged")
        reopened = collect(CONFIG, StaticAPI([issue()]), NOW, closed)
        self.assertEqual(reopened["projects"][0]["pull_requests"][0]["status"], "open")

    def test_identical_duplicates_are_deduplicated_but_conflicts_fail(self):
        item = issue()
        result = collect(CONFIG, StaticAPI([item, dict(item)]), NOW)
        self.assertEqual(result["totals"]["pull_requests"], 1)
        conflict = issue(title="Different")
        with self.assertRaisesRegex(CollectionError, "conflicting duplicate"):
            collect(CONFIG, StaticAPI([item, conflict]), NOW)

    def test_paginates_every_page(self):
        items = [issue(number=n, identifier=n) for n in range(1, 102)]
        api = StaticAPI(items)
        count, found = _fetch_window(api, CONFIG["profile"], date(2026, 1, 1), date(2026, 1, 2))
        self.assertEqual((count, len(found)), (101, 101))
        self.assertEqual([call[1]["page"] for call in api.calls], [1, 2])

    def test_temporal_partitioning_above_search_limit(self):
        one, two, three = issue(number=1), issue(number=2), issue(number=3)
        def window(_api, _profile, start, end):
            if start != end:
                return 3, []
            return (1, [one]) if start.day == 1 else (2, [two, three])
        with patch("scripts.external_contributions._fetch_window", side_effect=window), \
             patch("scripts.external_contributions.MAX_SEARCH_RESULTS", 2):
            found = _partitioned_search(object(), CONFIG["profile"], date(2026, 1, 1), date(2026, 1, 2))
        self.assertEqual(len(found), 3)

    def test_unsplittable_day_and_inconsistent_partition_fail_closed(self):
        with patch("scripts.external_contributions._fetch_window", return_value=(1001, [])):
            with self.assertRaisesRegex(CollectionError, "cannot be safely split"):
                _partitioned_search(object(), CONFIG["profile"], date(2026, 1, 1), date(2026, 1, 1))
        answers = [(3, []), (1, [issue()]), (1, [issue(number=2)])]
        with patch("scripts.external_contributions._fetch_window", side_effect=answers), \
             patch("scripts.external_contributions.MAX_SEARCH_RESULTS", 2):
            with self.assertRaisesRegex(CollectionError, "disagree"):
                _partitioned_search(object(), CONFIG["profile"], date(2026, 1, 1), date(2026, 1, 2))

    def test_incomplete_results_and_missing_previous_pr_fail_closed(self):
        with patch("scripts.external_contributions.time.sleep"):
            with self.assertRaisesRegex(CollectionError, "incomplete"):
                _partitioned_search(StaticAPI([issue()], incomplete=True), CONFIG["profile"],
                                    date(2026, 10, 11), date(2026, 10, 11))
        previous = collect(CONFIG, StaticAPI([issue()]), NOW)
        with self.assertRaisesRegex(CollectionError, "disappeared"):
            collect(CONFIG, StaticAPI([]), NOW, previous)

    def test_same_facts_preserve_published_sync_timestamp(self):
        previous = collect(CONFIG, StaticAPI([issue()]), NOW)
        later = datetime(2026, 10, 12, tzinfo=timezone.utc)
        current = collect(CONFIG, StaticAPI([issue()]), later, previous)
        self.assertEqual(current, previous)

    def test_projects_and_prs_have_stable_recency_order(self):
        items = [issue("older/repo", 1, updated="2026-01-02T10:00:00Z"),
                 issue("newer/repo", 2, created="2026-02-02T10:00:00Z",
                       updated="2026-02-03T10:00:00Z"),
                 issue("newer/repo", 3, created="2026-02-01T10:00:00Z",
                       updated="2026-02-01T11:00:00Z")]
        result = collect(CONFIG, StaticAPI(items), NOW)
        self.assertEqual([p["repository"] for p in result["projects"]],
                         ["newer/repo", "older/repo"])
        self.assertEqual([pr["number"] for pr in result["projects"][0]["pull_requests"]], [2, 3])

    def test_invalid_author_url_and_identity_are_rejected(self):
        cases = [issue(author="other"), {**issue(), "html_url": "https://evil.invalid/1"},
                 {**issue(), "id": 0}]
        for item in cases:
            with self.subTest(item=item):
                with self.assertRaises(CollectionError):
                    collect(CONFIG, StaticAPI([item]), NOW)


if __name__ == "__main__":
    unittest.main()
