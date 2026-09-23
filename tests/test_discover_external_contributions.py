"""Offline tests for discovery of new external open-source projects."""

import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.discover_external_contributions import discover, main
from scripts.external_contributions import CollectionError


LOGIN = "rodri-oliveira-dev"
CURATED = "SomeOrg/Curated"
NEW = "NewOrg/NewProject"
DATE = datetime(2026, 9, 23, 9, 0, tzinfo=timezone.utc)


def config():
    """Return a small valid selection of projects."""
    return {
        "schema_version": 1,
        "profile": LOGIN,
        "projects": [
            {
                "repository": CURATED,
                "name": "Curated",
                "pull_requests": [{"number": 1, "pt": "Descrição", "en": "Description"}],
            }
        ],
    }


def issue(repository, number, state="open", merged_at=None, author=LOGIN):
    """Model the GitHub Search PR fields consumed by the collector."""
    return {
        "repository_url": f"https://api.github.com/repos/{repository}",
        "number": number,
        "user": {"login": author},
        "state": state,
        "pull_request": {"merged_at": merged_at},
    }


def response(items, total=None, incomplete=False):
    """Build a complete or deliberately partial search page."""
    return {
        "items": items,
        "total_count": len(items) if total is None else total,
        "incomplete_results": incomplete,
    }


class FakeAPI:
    """Supply deterministic pages without contacting GitHub."""

    def __init__(self, pages):
        self.pages = pages
        self.queries = []

    def get(self, path, params):
        self.queries.append((path, params))
        result = self.pages[params["page"]]
        if isinstance(result, Exception):
            raise result
        return result


class DiscoveryTests(unittest.TestCase):
    """Verify the read-only candidate report and its fail-closed behavior."""

    def test_new_repository_is_discovered_but_curated_one_is_not(self):
        api = FakeAPI({1: response([
            issue(CURATED, 1),
            issue(NEW, 2, "closed", "2026-09-22T10:00:00Z"),
            issue(NEW, 3),
        ])})
        result = discover(config(), api, DATE)
        self.assertEqual(result["matching_public_prs"], 3)
        self.assertEqual(result["collected_at"], "2026-09-23T09:00:00Z")
        self.assertEqual([p["repository"] for p in result["candidate_repositories"]], [NEW])
        self.assertEqual(
            [p["status"] for p in result["candidate_repositories"][0]["pull_requests"]],
            ["merged", "open"],
        )
        self.assertIn(f"-user:{LOGIN}", api.queries[0][1]["q"])

    def test_no_candidates_is_valid(self):
        result = discover(config(), FakeAPI({1: response([issue(CURATED, 1)])}), DATE)
        self.assertEqual(result["candidate_repositories"], [])

    def test_zero_public_prs_is_valid(self):
        result = discover(config(), FakeAPI({1: response([])}), DATE)
        self.assertEqual(result["matching_public_prs"], 0)
        self.assertEqual(result["candidate_repositories"], [])

    def test_pagination_deduplicates_prs(self):
        first = [issue(NEW, n) for n in range(1, 101)]
        second = [issue(NEW, 100), issue(NEW, 101)]
        api = FakeAPI({1: response(first, 101), 2: response(second, 101)})
        result = discover(config(), api, DATE)
        self.assertEqual(len(result["candidate_repositories"][0]["pull_requests"]), 101)
        self.assertEqual([args["page"] for _, args in api.queries], [1, 2])

    def test_incomplete_search_fails_without_a_report(self):
        for page in (response([issue(NEW, 1)], incomplete=True),
                     response([issue(NEW, 1)], total=1001),
                     response([issue(NEW, 1)], total=2)):
            with self.subTest(page=page["total_count"]):
                with self.assertRaises(CollectionError):
                    discover(config(), FakeAPI({1: page}), DATE)

    def test_wrong_author_or_malformed_repository_rejected(self):
        for item in (
            issue(NEW, 1, author="SomeoneElse"),
            issue("NotASlash", 1),
        ):
            with self.subTest(item=item):
                with self.assertRaises(CollectionError):
                    discover(config(), FakeAPI({1: response([item])}), DATE)

    def test_conflicting_duplicate_rejected(self):
        first = [issue(NEW, n) for n in range(1, 101)]
        second = [issue(NEW, 100, state="closed"), issue(NEW, 101)]
        with self.assertRaisesRegex(CollectionError, "conflicting"):
            discover(config(), FakeAPI({
                1: response(first, total=101), 2: response(second, total=101)
            }), DATE)

    def test_failed_cli_preserves_previous_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings, output = root / "config.json", root / "candidates.json"
            settings.write_text(json.dumps(config()), encoding="utf-8")
            output.write_text("previous valid report\n", encoding="utf-8")
            api = FakeAPI({1: response([issue(NEW, 2)], incomplete=True)})
            with patch("scripts.discover_external_contributions.GitHubAPI", return_value=api):
                with patch.dict("os.environ", {"GITHUB_TOKEN": "example"}):
                    with patch("sys.stderr", new_callable=io.StringIO):
                        code = main(["--config", str(settings), "--output", str(output)])
            self.assertEqual(code, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous valid report\n")


if __name__ == "__main__":
    unittest.main()
