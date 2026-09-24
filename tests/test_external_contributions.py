"""Offline tests for the curated external-contributions collector."""

import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.external_contributions import (
    CollectionError,
    GitHubAPI,
    collect,
    load_config,
    main,
    write_snapshot,
)


REPO = "SomeOrg/SomeProject"
PROFILE = "rodri-oliveira-dev"
NOW = datetime(2026, 9, 23, 20, 0, tzinfo=timezone.utc)


def curated(repository=REPO, numbers=(10,)):
    return {
        "schema_version": 1,
        "profile": PROFILE,
        "projects": [
            {
                "repository": repository,
                "name": "External project",
                "pull_requests": [
                    {"number": number, "pt": "Texto", "en": "Text"}
                    for number in numbers
                ],
            }
        ],
    }


def issue(number, state="open", merged_at=None, repository=REPO, author=PROFILE):
    return {
        "number": number,
        "state": state,
        "repository_url": f"https://api.github.com/repos/{repository}",
        "user": {"login": author},
        "pull_request": {"merged_at": merged_at},
    }


def search(items, total=None, incomplete=False):
    return {
        "total_count": len(items) if total is None else total,
        "incomplete_results": incomplete,
        "items": items,
    }


class FakeAPI:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, path, params):
        self.calls.append((path, dict(params)))
        repo = params["q"].split("repo:", 1)[1]
        response = self.pages.get((repo, params["page"]))
        if isinstance(response, BaseException):
            raise response
        if response is None:
            raise AssertionError(f"Unexpected API page: {repo} {params['page']}")
        return response


class CollectorTests(unittest.TestCase):
    def test_merged_open_and_closed_without_merge_are_distinct(self):
        api = FakeAPI({
            (REPO, 1): search([
                issue(10, "closed", "2026-09-01T10:00:00Z"),
                issue(11, "open"),
                issue(12, "closed"),
            ]),
        })
        result = collect(curated(numbers=(10, 11, 12)), api, NOW)
        self.assertEqual(result["collected_at"], "2026-09-23T20:00:00Z")
        self.assertEqual(result["totals"], {
            "authored_prs": 3,
            "merged_prs": 1,
            "open_prs": 1,
            "closed_unmerged_prs": 1,
            "repositories_with_merged_prs": 1,
        })
        self.assertEqual(
            [pr["status"] for pr in result["projects"][0]["reference_prs"]],
            ["merged", "open", "closed_unmerged"],
        )
        self.assertEqual(result["latest_merged_at"], "2026-09-01T10:00:00Z")

    def test_pagination_deduplicates_repeated_pr_number(self):
        first = [issue(number) for number in range(1, 101)]
        api = FakeAPI({
            (REPO, 1): search(first, total=101),
            (REPO, 2): search([issue(100), issue(101)], total=101),
        })
        result = collect(curated(numbers=(101,)), api, NOW)
        self.assertEqual(result["totals"]["authored_prs"], 101)
        self.assertEqual([call[1]["page"] for call in api.calls], [1, 2])
        self.assertTrue(all("is:public" in call[1]["q"].split() for call in api.calls))
        self.assertEqual(result["projects"][0]["reference_prs"][0]["number"], 101)

    def test_incomplete_pagination_rejects_false_totals(self):
        api = FakeAPI({(REPO, 1): search([issue(10)], total=2)})
        with self.assertRaisesRegex(CollectionError, "pagination is incomplete"):
            collect(curated(), api, NOW)

    def test_search_flags_incomplete_results(self):
        api = FakeAPI({(REPO, 1): search([issue(10)], incomplete=True)})
        with self.assertRaisesRegex(CollectionError, "incomplete"):
            collect(curated(), api, NOW)

    def test_search_over_1000_is_rejected(self):
        api = FakeAPI({(REPO, 1): search([issue(10)], total=1001)})
        with self.assertRaisesRegex(CollectionError, "result limit"):
            collect(curated(), api, NOW)

    def test_no_results_with_curated_reference_rejected(self):
        api = FakeAPI({(REPO, 1): search([])})
        with self.assertRaisesRegex(CollectionError, "reference PR"):
            collect(curated(), api, NOW)

    def test_conflicting_duplicate_is_rejected(self):
        api = FakeAPI({
            (REPO, 1): search(
                [issue(number) for number in range(1, 101)], total=101
            ),
            (REPO, 2): search([
                issue(100, "closed", "2026-09-01T10:00:00Z"),
                issue(101),
            ], total=101),
        })
        with self.assertRaisesRegex(CollectionError, "conflicting duplicate"):
            collect(curated(), api, NOW)

    def test_wrong_author_and_wrong_repository_are_rejected(self):
        for entry in (
            issue(10, author="someone-else"),
            issue(10, repository="Another/Repository"),
        ):
            with self.subTest(entry=entry):
                api = FakeAPI({(REPO, 1): search([entry])})
                with self.assertRaisesRegex(CollectionError, "unexpected PR or author"):
                    collect(curated(), api, NOW)

    def test_merged_pr_cannot_still_be_open(self):
        api = FakeAPI({
            (REPO, 1): search([issue(10, "open", "2026-09-01T10:00:00Z")]),
        })
        with self.assertRaisesRegex(CollectionError, "inconsistent"):
            collect(curated(), api, NOW)

    def test_curated_own_repo_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(curated(repository="rodri-oliveira-dev/AnotherProject")),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CollectionError, "Profile-owned"):
                load_config(path)

    def test_duplicate_repository_and_reference_number_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = curated(numbers=(10, 10))
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(CollectionError, "curated PR number"):
                load_config(path)
            config = curated()
            config["projects"].append(dict(config["projects"][0]))
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(CollectionError, "Duplicate curated repository"):
                load_config(path)

    def test_missing_token_does_not_call_api(self):
        with self.assertRaisesRegex(CollectionError, "GITHUB_TOKEN is required"):
            GitHubAPI("")

    def test_http_error_does_not_expose_secret(self):
        def denied(request, timeout):
            self.assertIn("Bearer my-secret", request.get_header("Authorization"))
            raise HTTPError(request.full_url, 403, "denied", None, None)

        with self.assertRaisesRegex(CollectionError, "HTTP 403") as caught:
            GitHubAPI("my-secret", opener=denied).get("/search/issues", {"q": "test"})
        self.assertNotIn("my-secret", str(caught.exception))

    def test_timeout_does_not_expose_secret(self):
        def timed_out(request, timeout):
            raise TimeoutError("Request timeout")

        with self.assertRaisesRegex(CollectionError, "retry limit") as caught:
            GitHubAPI("my-secret", opener=timed_out, max_attempts=1).get("/search/issues", {"q": "test"})
        self.assertNotIn("my-secret", str(caught.exception))

    def test_failed_collection_never_overwrites_last_valid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config_file = base / "config.json"
            output = base / "snapshot.json"
            config_file.write_text(json.dumps(curated()), encoding="utf-8")
            output.write_text("previous valid snapshot\n", encoding="utf-8")
            broken = FakeAPI({(REPO, 1): search([issue(10)], total=2)})
            with patch("scripts.external_contributions.GitHubAPI", return_value=broken):
                with patch.dict("os.environ", {"GITHUB_TOKEN": "example"}):
                    with patch("sys.stderr", new_callable=io.StringIO):
                        exit_code = main(["--config", str(config_file), "--output", str(output)])
            self.assertEqual(exit_code, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous valid snapshot\n")

    def test_atomic_snapshot_writes_utf8_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "subdir" / "snapshot.json"
            write_snapshot(output, {"message": "contribuição"})
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                {"message": "contribuição"},
            )


if __name__ == "__main__":
    unittest.main()
