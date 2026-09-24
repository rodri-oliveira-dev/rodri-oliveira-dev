"""Regression tests for the optional discovery/curated README isolation."""

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.prepare_discovery_report import UNAVAILABLE, main, prepare_report


class DiscoveryIsolationTests(unittest.TestCase):
    def test_failure_is_unavailable_not_empty_candidates(self):
        for outcome in ("failure", "skipped", "cancelled", "timed_out"):
            with self.subTest(outcome=outcome):
                result = prepare_report(outcome, Path("/does-not-exist"))
                self.assertEqual(result, UNAVAILABLE)
                self.assertNotIn("candidate_repositories", result)

    def test_success_preserves_candidate_report(self):
        payload = {
            "schema_version": 1,
            "profile": "rodri-oliveira-dev",
            "candidate_repositories": [{"repository": "External/Repo", "pull_requests": []}],
        }
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "candidates.json"
            src.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(prepare_report("success", src), payload)

    def test_success_with_zero_candidates_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "candidates.json"
            payload = {"schema_version": 1, "candidate_repositories": []}
            src.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(prepare_report("success", src), payload)

    def test_success_with_missing_or_corrupt_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "candidates.json"
            with self.assertRaisesRegex(ValueError, "no valid"):
                prepare_report("success", src)
            for invalid in ("{", "{}", '{"schema_version":1,"candidate_repositories":{}}'):
                src.write_text(invalid, encoding="utf-8")
                with self.assertRaises(ValueError):
                    prepare_report("success", src)

    def test_failed_discovery_cli_writes_unavailable_status_without_fake_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            with patch("sys.stdout", new_callable=io.StringIO):
                code = main([
                    "--discovery-result", "failure",
                    "--input", str(Path(folder) / "missing.json"),
                    "--output", str(path),
                ])
            self.assertEqual(code, 0)
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "unavailable")
            self.assertNotIn("candidate_repositories", report)

    def test_missing_success_report_does_not_replace_previous_valid_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            path.write_text('{"candidate_repositories":[]}\n', encoding="utf-8")
            with patch("sys.stderr", new_callable=io.StringIO):
                code = main([
                    "--discovery-result", "success",
                    "--input", str(Path(folder) / "missing.json"),
                    "--output", str(path),
                ])
            self.assertEqual(code, 1)
            self.assertEqual(path.read_text(encoding="utf-8"), '{"candidate_repositories":[]}\n')


if __name__ == "__main__":
    unittest.main()
