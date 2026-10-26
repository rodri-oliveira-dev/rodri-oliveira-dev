"""Keep the bilingual profile presentation usable in GitHub's mobile Markdown viewer."""

import unittest
from pathlib import Path

PROJECTS = (
    "adr-guard",
    "Dapper-FluentMap",
    "Repo2C4",
    "poc-arquitetura",
    "ReliableWebhooks",
    "complexity-analyzers",
)
BOARD_URL = "https://github.com/users/rodri-oliveira-dev/projects/1/views/1"


class ProfileReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {
            "pt": Path("README.md").read_text(encoding="utf-8"),
            "en": Path("README.en.md").read_text(encoding="utf-8"),
        }

    def test_both_versions_use_a_single_column_project_layout(self):
        for language, content in self.documents.items():
            with self.subTest(language=language):
                self.assertNotIn("| --- |", content)
                self.assertEqual(content.count("### ["), len(PROJECTS))
                self.assertNotIn("github-stats-extended.vercel.app", content)
                self.assertNotIn(BOARD_URL, content)
                self.assertIn('src="assets/brand/ro-architect-mark.png"', content)

    def test_project_highlights_are_present_and_consistently_ordered(self):
        for language, content in self.documents.items():
            with self.subTest(language=language):
                positions = [
                    content.index(f"https://github.com/rodri-oliveira-dev/{project})")
                    for project in PROJECTS
                ]
                self.assertEqual(positions, sorted(positions))

    def test_each_language_links_to_its_own_external_contributions_catalog(self):
        self.assertIn("(docs/open-source-contributions.md)", self.documents["pt"])
        self.assertIn("(docs/open-source-contributions.en.md)", self.documents["en"])
        self.assertIn("[English](README.en.md)", self.documents["pt"])
        self.assertIn("[Português](README.md)", self.documents["en"])

    def test_professional_links_and_governance_remain_available(self):
        common = (
            "https://rodri-oliveira-dev.github.io/",
            "https://www.linkedin.com/in/rodri-oliveira-dev",
            "https://www.nuget.org/profiles/rodri-oliveira-dev",
            "https://github.com/rodri-oliveira-dev/.github",
        )
        for language, content in self.documents.items():
            with self.subTest(language=language):
                for url in common:
                    self.assertIn(url, content)
        self.assertIn("Café com código", self.documents["pt"])
        self.assertIn("https://dev.to/rodri-oliveira-dev", self.documents["en"])


if __name__ == "__main__":
    unittest.main()
