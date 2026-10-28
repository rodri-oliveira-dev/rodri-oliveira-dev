import unittest
from pathlib import Path


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(".github/workflows/external-contributions.yml").read_text(encoding="utf-8")

    def test_daily_schedule_and_manual_dispatch_remain(self):
        self.assertIn('cron: "0 9 * * *"', self.source)
        self.assertIn("workflow_dispatch:", self.source)

    def test_only_proposal_job_has_write_permissions(self):
        before, proposal = self.source.split("  propose:\n", 1)
        self.assertNotIn("contents: write", before)
        self.assertIn("contents: write", proposal)
        self.assertIn("pull-requests: write", proposal)

    def test_global_collection_is_required_before_publication(self):
        self.assertIn("--previous .github/external-contributions-catalog.json", self.source)
        self.assertIn("needs: synchronize", self.source)
        self.assertNotIn("external-contributions-review.json", self.source)
        self.assertIn("include-hidden-files: true", self.source)

    def test_spanish_catalog_is_rendered_and_checked_twice(self):
        self.assertIn("--output-es preview/docs/open-source-contributions.es.md", self.source)
        self.assertIn("cmp preview/docs/open-source-contributions.es.md", self.source)
        self.assertIn("- docs/open-source-contributions.es.md", self.source)
        self.assertIn("- README.es.md", self.source)

    def test_concurrency_and_main_gate_are_present(self):
        self.assertIn("concurrency:", self.source)
        self.assertIn("github.ref == 'refs/heads/main'", self.source)
        self.assertIn("scripts/propose_external_contributions.py", self.source)


if __name__ == "__main__":
    unittest.main()
