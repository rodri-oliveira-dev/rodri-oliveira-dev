import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.render_external_contributions import RenderError, render_catalog, validate_snapshot, write_updates


def snapshot(title="Fix [unsafe] *markdown* <tag>"):
    pr = {"id": 10, "number": 7, "url": "https://github.com/acme/widget/pull/7",
          "title": title, "status": "merged", "created_at": "2026-01-01T10:00:00Z",
          "updated_at": "2026-01-03T10:00:00Z", "merged_at": "2026-01-02T10:00:00Z"}
    return {"schema_version": 2, "profile": "rodri-oliveira-dev",
            "scope": "All public PRs authored by this profile in repositories owned by others",
            "last_successful_sync": "2026-10-11T12:00:00Z",
            "totals": {"repositories": 1, "pull_requests": 1, "merged": 1, "open": 0, "closed_unmerged": 0},
            "projects": [{"repository": "acme/widget", "url": "https://github.com/acme/widget",
                          "activity_at": "2026-01-03T10:00:00Z",
                          "totals": {"pull_requests": 1, "merged": 1, "open": 0, "closed_unmerged": 0},
                          "pull_requests": [pr]}]}


class RendererTests(unittest.TestCase):
    def test_bilingual_catalogs_share_facts_but_not_interface_text(self):
        data = snapshot("Original PR title")
        pt, en = render_catalog(data, "pt"), render_catalog(data, "en")
        for rendered in (pt, en):
            self.assertIn("Original PR title", rendered)
            self.assertIn("https://github.com/acme/widget/pull/7", rendered)
        self.assertIn("Integrado", pt)
        self.assertIn("Merged", en)
        self.assertIn("Índice de projetos", pt)
        self.assertIn("Project index", en)

    def test_closed_state_uses_consistent_portuguese_terminology(self):
        data = snapshot()
        pr = data["projects"][0]["pull_requests"][0]
        pr["status"], pr["merged_at"] = "closed_unmerged", None
        data["projects"][0]["totals"].update(merged=0, closed_unmerged=1)
        data["totals"].update(merged=0, closed_unmerged=1)
        rendered = render_catalog(data, "pt")
        self.assertIn("Fechado sem integração", rendered)
        self.assertNotIn("Fechado sem merge", rendered)

    def test_untrusted_markdown_is_escaped(self):
        rendered = render_catalog(snapshot(), "en")
        self.assertIn(r"Fix \[unsafe\] \*markdown\* &lt;tag&gt;", rendered)
        self.assertNotIn("<tag>", rendered)

    def test_invalid_order_and_totals_are_rejected(self):
        data = snapshot()
        data["totals"]["open"] = 1
        with self.assertRaisesRegex(RenderError, "Aggregate"):
            validate_snapshot(data)

    def test_failure_writing_second_language_restores_both_files(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "pt.md", Path(directory) / "en.md"
            first.write_text("old pt", encoding="utf-8")
            second.write_text("old en", encoding="utf-8")
            real_replace = __import__("os").replace
            stage_replacements = 0
            def failing_replace(source, destination):
                nonlocal stage_replacements
                if ".stage-" in str(source):
                    stage_replacements += 1
                    if stage_replacements == 2:
                        raise OSError("disk failure")
                return real_replace(source, destination)
            with patch("scripts.render_external_contributions.os.replace", side_effect=failing_replace):
                with self.assertRaisesRegex(RenderError, "rollback"):
                    write_updates({first: "new pt", second: "new en"})
            self.assertEqual(first.read_text(encoding="utf-8"), "old pt")
            self.assertEqual(second.read_text(encoding="utf-8"), "old en")

    def test_same_snapshot_renders_identically(self):
        data = snapshot()
        self.assertEqual(render_catalog(data, "pt"), render_catalog(data, "pt"))


if __name__ == "__main__":
    unittest.main()
