"""Guard the deployment workflow job graph and production entrypoint."""

import unittest
from pathlib import Path


def jobs():
    """Extract top-level job sections from the current checked-out workflow."""
    source = Path(".github/workflows/external-contributions.yml").read_text(encoding="utf-8")
    names = ("validate", "collect", "discover", "render", "propose")
    result = {}
    for index, name in enumerate(names):
        begin = source.index("\n  " + name + ":\n") + 1
        if index + 1 < len(names):
            end = source.index("\n  " + names[index + 1] + ":\n", begin)
        else:
            end = len(source)
        result[name] = source[begin:end]
    return result


class WorkflowContractTests(unittest.TestCase):
    """Reject regressions in fault isolation and write permissions."""

    def test_discovery_is_separate_and_reports_unavailable(self):
        workflow = jobs()
        self.assertIn("scripts/external_contributions.py", workflow["collect"])
        self.assertNotIn("scripts/discover_external_contributions.py", workflow["collect"])
        self.assertIn("scripts/discover_external_contributions.py", workflow["discover"])
        self.assertIn('echo "status=unavailable" >> "$GITHUB_OUTPUT"', workflow["discover"])
        self.assertIn("if: ${{ steps.discovery.outputs.status == 'success' }}", workflow["discover"])

    def test_render_survives_optional_failure_and_rejects_curated_failure(self):
        workflow = jobs()
        self.assertIn("needs: [collect, discover]", workflow["render"])
        self.assertIn("always() && needs.collect.result == 'success'", workflow["render"])
        self.assertIn("needs.discover.outputs.status == 'success'", workflow["render"])
        self.assertIn("--discovery-result", workflow["render"])
        self.assertIn('discovery.get("status") == "unavailable"', workflow["render"])
        self.assertNotIn('discovery.get("candidate_repositories", [])', workflow["render"])

    def test_propose_has_main_gate_and_uses_tested_script(self):
        workflow = jobs()
        self.assertIn("needs.render.result == 'success'", workflow["propose"])
        self.assertIn("github.ref == 'refs/heads/main'", workflow["propose"])
        self.assertIn("inputs.publish == true", workflow["propose"])
        self.assertIn("ref: ${{ github.sha }}", workflow["propose"])
        self.assertIn("python3 scripts/propose_external_contributions.py", workflow["propose"])
        self.assertIn("contents: write", workflow["propose"])
        for job in ("validate", "collect", "discover", "render"):
            self.assertNotIn("contents: write", workflow[job])

    def test_schedule_uses_nine_utc_daily(self):
        source = Path(".github/workflows/external-contributions.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "0 9 * * *"', source)


if __name__ == "__main__":
    unittest.main()
