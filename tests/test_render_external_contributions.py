import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.render_external_contributions import (
    RenderError, _anchor, load_snapshot, render_catalog, validate_snapshot, write_updates,
)


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
    def test_repository_anchors_preserve_punctuation_identity(self):
        dotted = _anchor("owner/a.b")
        dashed = _anchor("owner/a-b")
        self.assertNotEqual(dotted, dashed)
        self.assertEqual(dotted, _anchor("OWNER/A.B"))
        self.assertRegex(dotted, r"^repository-[0-9a-f]+$")

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

    def test_repository_prs_are_rendered_as_a_table_in_both_languages(self):
        data = snapshot("Fix a | b")
        for language, status, date_opened, date_merged in (
                ("pt", "Integrado", "01/01/2026", "02/01/2026"),
                ("en", "Merged", "2026-01-01", "2026-01-02")):
            rendered = render_catalog(data, language)
            self.assertIn("| --- | --- | --- | --- |", rendered)
            self.assertIn(
                f"| [#7](https://github.com/acme/widget/pull/7) — Fix a \\| b | {status} | {date_opened} | {date_merged} |",
                rendered,
            )
            self.assertNotIn("\n- [#7](", rendered)

    def test_non_merged_prs_show_no_merge_date(self):
        for status, totals_key, label in (("open", "open", "Aberto"),
                                          ("closed_unmerged", "closed_unmerged", "Fechado sem integração")):
            data = snapshot("Non-merged change")
            pr = data["projects"][0]["pull_requests"][0]
            pr["status"], pr["merged_at"] = status, None
            data["projects"][0]["totals"].update(merged=0, **{totals_key: 1})
            data["totals"].update(merged=0, **{totals_key: 1})
            rendered = render_catalog(data, "pt")
            self.assertIn(
                f"| [#7](https://github.com/acme/widget/pull/7) — Non-merged change | {label} | 01/01/2026 | — |",
                rendered,
            )

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


    def test_dashboard_sections_navigation_and_collapsible_history(self):
        data = snapshot("Document a feature")
        for language, titles in (
            ("pt", ("Projetos em destaque", "Atividade recente", "Índice de projetos", "Contribuições por repositório")),
            ("en", ("Featured projects", "Recent activity", "Project index", "Contributions by repository")),
        ):
            with self.subTest(language=language):
                rendered = render_catalog(data, language)
                for title in titles:
                    self.assertIn(f"## {title}", rendered)
                for section in ("featured-projects", "recent-activity", "project-index", "contribution-history"):
                    self.assertIn(f'<a id="{section}"></a>', rendered)
                    self.assertIn(f"(#{section})", rendered)
                self.assertEqual(rendered.count("<details>"), 1)
                self.assertEqual(rendered.count("</details>"), 1)
                self.assertIn("<summary><strong>acme/widget</strong> · 1 PR", rendered)
                self.assertIn(f'<a id="{_anchor("acme/widget")}"></a>', rendered)
                self.assertIn("**100%**", rendered)
                self.assertIn("▰" * 20, rendered)
                self.assertNotIn("1 PRs", rendered)

    def test_featured_projects_come_from_snapshot_only(self):
        rendered = render_catalog(snapshot(), "en")
        featured = rendered.split("## Featured projects", 1)[1].split("## Recent activity", 1)[0]
        self.assertIn("**[acme/widget](https://github.com/acme/widget)**", featured)
        self.assertNotIn("likec4/likec4", featured)
        self.assertIn("**1 PR** · 1 merged", featured)

    def test_recent_activity_uses_merge_timestamp_not_display_order(self):
        data = snapshot("First merged change")
        project = data["projects"][0]
        project["pull_requests"].append({
            "id": 11, "number": 6, "url": "https://github.com/acme/widget/pull/6",
            "title": "More recently merged change", "status": "merged",
            "created_at": "2025-12-31T10:00:00Z", "updated_at": "2026-01-03T10:00:00Z",
            "merged_at": "2026-01-03T09:00:00Z",
        })
        project["totals"].update(pull_requests=2, merged=2)
        data["totals"].update(pull_requests=2, merged=2)
        rendered = render_catalog(data, "en")
        recent = rendered.split("## Recent activity", 1)[1].split("## Project index", 1)[0]
        self.assertLess(recent.index("/pull/6"), recent.index("/pull/7"))
        self.assertEqual(recent.count("https://github.com/acme/widget/pull/"), 2)

    def test_empty_catalog_does_not_divide_by_zero_or_render_details(self):
        data = snapshot()
        data["projects"] = []
        data["totals"] = {
            "repositories": 0, "pull_requests": 0, "merged": 0,
            "open": 0, "closed_unmerged": 0,
        }
        for language in ("pt", "en"):
            with self.subTest(language=language):
                rendered = render_catalog(data, language)
                self.assertIn("**0%**", rendered)
                self.assertIn("▱" * 20, rendered)
                self.assertNotIn("<details>", rendered)

    def test_published_bilingual_catalogs_match_the_renderer(self):
        data = load_snapshot(Path(".github/external-contributions-catalog.json"))
        for language, path in (
            ("pt", Path("docs/open-source-contributions.md")),
            ("en", Path("docs/open-source-contributions.en.md")),
        ):
            with self.subTest(language=language):
                self.assertEqual(path.read_text(encoding="utf-8"), render_catalog(data, language))

    def test_same_snapshot_renders_identically(self):
        data = snapshot()
        self.assertEqual(render_catalog(data, "pt"), render_catalog(data, "pt"))


if __name__ == "__main__":
    unittest.main()
