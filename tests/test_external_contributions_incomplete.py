import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import date
from pathlib import Path
from unittest.mock import call, patch

from scripts.external_contributions import (
    CollectionError, _fetch_window, _partitioned_search, main,
)


START = date(2026, 10, 21)
END = date(2026, 10, 22)
PROFILE = "rodri-oliveira-dev"


def response(items=None, *, count=None, incomplete=False):
    items = [] if items is None else items
    return {"total_count": len(items) if count is None else count,
            "items": items, "incomplete_results": incomplete}


class SequenceAPI:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = []

    def get(self, path, params):
        self.calls.append((path, params.copy()))
        return next(self.results)


class SplitAPI:
    def __init__(self, incomplete_parent=True):
        self.calls = []
        self.incomplete_parent = incomplete_parent

    def get(self, path, params):
        self.calls.append(params.copy())
        window = params["q"].split("created:", 1)[1]
        if window == "2026-10-21..2026-10-22" and self.incomplete_parent:
            return response([{"partial": True}], count=2, incomplete=True)
        if window == "2026-10-21..2026-10-21":
            return response([{"day": 21}])
        if window == "2026-10-22..2026-10-22":
            return response([{"day": 22}])
        raise AssertionError(f"Unexpected date range: {window}")


class IncompleteSearchTests(unittest.TestCase):
    def test_retries_incomplete_http_200_then_accepts_complete_response(self):
        api = SequenceAPI([
            response([{"partial": True}], count=1, incomplete=True),
            response([{"complete": True}], count=1),
        ])
        stderr = io.StringIO()
        with patch("scripts.external_contributions.time.sleep") as sleep, redirect_stderr(stderr):
            count, items = _fetch_window(api, PROFILE, START, END)
        self.assertEqual((count, items), (1, [{"complete": True}]))
        self.assertEqual(len(api.calls), 2)
        sleep.assert_called_once_with(1.0)
        self.assertIn("total_count=1", stderr.getvalue())
        self.assertIn("items_count=1", stderr.getvalue())
        self.assertIn("incomplete_results=True", stderr.getvalue())
        self.assertIn("page=1", stderr.getvalue())

    def test_persistent_incomplete_search_splits_into_complete_disjoint_days(self):
        api = SplitAPI()
        with patch("scripts.external_contributions.time.sleep") as sleep, redirect_stderr(io.StringIO()):
            items = _partitioned_search(api, PROFILE, START, END)
        self.assertEqual(items, [{"day": 21}, {"day": 22}])
        self.assertEqual(len(api.calls), 5)  # 3 parent retries, 2 complete day windows
        self.assertEqual(sleep.call_args_list, [call(1.0), call(2.0)])

    def test_single_day_persistent_incomplete_results_fail_closed(self):
        api = SequenceAPI([response([{"partial": True}], incomplete=True)] * 3)
        with patch("scripts.external_contributions.time.sleep") as sleep:
            with self.assertRaisesRegex(CollectionError, "single day.*cannot safely split") as raised:
                _partitioned_search(api, PROFILE, START, START)
        self.assertIn("total_count=1", str(raised.exception))
        self.assertIn("items_count=1", str(raised.exception))
        self.assertEqual(len(api.calls), 3)
        self.assertEqual(sleep.call_args_list, [call(1.0), call(2.0)])

    def test_malformed_payload_is_rejected_without_retry_or_partitioning(self):
        api = SequenceAPI([{"total_count": None, "items": [], "incomplete_results": False}])
        with patch("scripts.external_contributions.time.sleep") as sleep:
            with self.assertRaisesRegex(CollectionError, "invalid results") as raised:
                _partitioned_search(api, PROFILE, START, END)
        self.assertIn("total_count=None", str(raised.exception))
        self.assertEqual(len(api.calls), 1)
        sleep.assert_not_called()

    def test_incomplete_second_page_is_retried(self):
        page_one = response([{"page": 1}] * 100, count=101)
        page_two_incomplete = response([{"partial": True}], count=101, incomplete=True)
        page_two_complete = response([{"page": 2}], count=101)
        api = SequenceAPI([page_one, page_two_incomplete, page_two_complete])
        with patch("scripts.external_contributions.time.sleep") as sleep, redirect_stderr(io.StringIO()):
            count, items = _fetch_window(api, PROFILE, START, END)
        self.assertEqual((count, len(items)), (101, 101))
        self.assertEqual([params["page"] for _, params in api.calls], [1, 2, 2])
        sleep.assert_called_once_with(1.0)

    def test_failed_collection_preserves_previous_and_output_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            config, previous, output = (directory / name for name in
                                        ("config.json", "previous.json", "preview.json"))
            config.write_text(json.dumps({"schema_version": 2, "profile": PROFILE}), encoding="utf-8")
            previous.write_text('{"existing":"catalog"}', encoding="utf-8")
            output.write_text('{"existing":"preview"}', encoding="utf-8")
            class AlwaysIncomplete:
                def get(self, _path, _params):
                    return response([], incomplete=True)
            with (patch("scripts.external_contributions.GitHubAPI", return_value=AlwaysIncomplete()),
                  patch("scripts.external_contributions.GITHUB_EPOCH", START),
                  patch("scripts.external_contributions.time.sleep"),
                  redirect_stderr(io.StringIO())):
                status = main(["--config", str(config), "--previous", str(previous),
                               "--output", str(output)])
            self.assertEqual(status, 1)
            self.assertEqual(json.loads(previous.read_text(encoding="utf-8")), {"existing": "catalog"})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"existing": "preview"})


if __name__ == "__main__":
    unittest.main()
