"""End-to-end offline regression for isolation of optional discovery failures."""

import tempfile
import unittest
from pathlib import Path

from scripts.prepare_discovery_report import prepare_report
from scripts.render_external_contributions import RenderError, prepare_updates, write_updates


BEGIN = "<!-- EXTERNAL_CONTRIBUTIONS:START -->"
END = "<!-- EXTERNAL_CONTRIBUTIONS:END -->"


def config():
    """Define one public external project and a single curated reference."""
    return {
        "schema_version": 1,
        "profile": "profile-owner",
        "projects": [
            {
                "repository": "External/Project",
                "name": "Project",
                "pull_requests": [
                    {"number": 7, "pt": "Contribuição curada.", "en": "Curated contribution."},
                ],
            },
        ],
    }


def snapshot():
    """Return a verified curated snapshot, independent of global discovery."""
    return {
        "schema_version": 1,
        "profile": "profile-owner",
        "scope": "Public PRs authored by this profile in the curated external repositories only",
        "repositories": 1,
        "collected_at": "2026-09-23T09:00:00Z",
        "latest_merged_at": "2026-09-22T09:00:00Z",
        "totals": {
            "authored_prs": 1,
            "merged_prs": 1,
            "open_prs": 0,
            "closed_unmerged_prs": 0,
            "repositories_with_merged_prs": 1,
        },
        "projects": [
            {
                "repository": "External/Project",
                "authored_prs": 1,
                "merged_prs": 1,
                "open_prs": 0,
                "closed_unmerged_prs": 0,
                "reference_prs": [
                    {
                        "number": 7,
                        "url": "https://github.com/External/Project/pull/7",
                        "status": "merged",
                        "merged_at": "2026-09-22T09:00:00Z",
                    },
                ],
            },
        ],
    }


class IndependentFlowTests(unittest.TestCase):
    """A failed optional search must not fabricate zeros or block valid Markdown."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.pt = self.folder / "README.md"
        self.en = self.folder / "README.en.md"
        for filename in (self.pt, self.en):
            filename.write_text(
                "# Profile\n\n" + BEGIN + "\n\nOld\n\n" + END + "\n\nEditorial footer\n",
                encoding="utf-8",
            )

    def test_global_discovery_failure_does_not_block_curated_bilingual_render(self):
        report = prepare_report("unavailable", self.folder / "missing-candidates.json")
        self.assertEqual(report["status"], "unavailable")
        self.assertNotIn("candidate_repositories", report)
        changed = prepare_updates(
            config(), snapshot(), {"pt": self.pt, "en": self.en},
        )
        self.assertEqual(set(changed), {self.pt, self.en})
        write_updates(changed)
        self.assertIn("1 no total, 1 integrados", self.pt.read_text(encoding="utf-8"))
        self.assertIn("1 total, 1 merged", self.en.read_text(encoding="utf-8"))
        self.assertTrue(self.pt.read_text(encoding="utf-8").endswith("Editorial footer\n"))
        self.assertTrue(self.en.read_text(encoding="utf-8").endswith("Editorial footer\n"))

    def test_curated_failure_blocks_both_languages_even_when_discovery_succeeds(self):
        payload = snapshot()
        payload["totals"]["merged_prs"] = 0
        before = self.pt.read_bytes()
        with self.assertRaises(RenderError):
            prepare_updates(config(), payload, {"pt": self.pt, "en": self.en})
        self.assertEqual(self.pt.read_bytes(), before)
        self.assertEqual(self.en.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
