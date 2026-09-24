"""Offline tests for bilingual, idempotent external-contributions Markdown."""

import copy
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.render_external_contributions import (
    END,
    START,
    RenderError,
    load_snapshot,
    main,
    prepare_updates,
    render_block,
    write_updates,
)


def config():
    return {
        "schema_version": 1,
        "profile": "rodri-oliveira-dev",
        "projects": [
            {
                "repository": "SomeOrg/ProjectOne",
                "name": "Project | One",
                "pull_requests": [
                    {"number": 10, "pt": "Correção de timeout | com testes.", "en": "Timeout fix | with tests."},
                    {"number": 11, "pt": "Proposta de teste.", "en": "Proposed test."},
                    {"number": 12, "pt": "Proposta encerrada.", "en": "Proposal closed."},
                ],
            },
            {
                "repository": "AnotherOrg/ProjectTwo",
                "name": "Project Two",
                "pull_requests": [
                    {"number": 20, "pt": "Documentação em pt-BR.", "en": "Brazilian Portuguese documentation."},
                ],
            },
        ],
    }


def snapshot(timestamp="2026-09-23T20:00:00Z"):
    return {
        "schema_version": 1,
        "profile": "rodri-oliveira-dev",
        "scope": "Public PRs authored by this profile in the curated external repositories only",
        "repositories": 2,
        "collected_at": timestamp,
        "latest_merged_at": "2026-09-21T11:10:46Z",
        "totals": {
            "authored_prs": 5,
            "merged_prs": 2,
            "open_prs": 2,
            "closed_unmerged_prs": 1,
            "repositories_with_merged_prs": 2,
        },
        "projects": [
            {
                "repository": "SomeOrg/ProjectOne",
                "authored_prs": 4,
                "merged_prs": 1,
                "open_prs": 2,
                "closed_unmerged_prs": 1,
                "reference_prs": [
                    {
                        "number": 10,
                        "url": "https://github.com/SomeOrg/ProjectOne/pull/10",
                        "status": "merged",
                        "merged_at": "2026-09-21T11:10:46Z",
                    },
                    {
                        "number": 11,
                        "url": "https://github.com/SomeOrg/ProjectOne/pull/11",
                        "status": "open",
                        "merged_at": None,
                    },
                    {
                        "number": 12,
                        "url": "https://github.com/SomeOrg/ProjectOne/pull/12",
                        "status": "closed_unmerged",
                        "merged_at": None,
                    },
                ],
            },
            {
                "repository": "AnotherOrg/ProjectTwo",
                "authored_prs": 1,
                "merged_prs": 1,
                "open_prs": 0,
                "closed_unmerged_prs": 0,
                "reference_prs": [
                    {
                        "number": 20,
                        "url": "https://github.com/AnotherOrg/ProjectTwo/pull/20",
                        "status": "merged",
                        "merged_at": "2026-09-08T07:39:23Z",
                    },
                ],
            },
        ],
    }


def readme(language):
    heading = "## Contribuições open source" if language == "pt" else "## Open-source contributions"
    return (
        "# Profile\n\n" + heading +
        "\n\nTexto editorial fora dos marcadores.\n\n" +
        START + "\n\nConteúdo anterior.\n\n" + END +
        "\n\nTexto editorial final.\n\n## Próxima seção\n\nNão modificar.\n"
    )


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pt = self.root / "README.md"
        self.en = self.root / "README.en.md"
        self.pt.write_text(readme("pt"), encoding="utf-8")
        self.en.write_text(readme("en"), encoding="utf-8")
        self.paths = {"pt": self.pt, "en": self.en}
        self.cfg = config()
        self.data = snapshot()

    def _update(self, data=None):
        writes = prepare_updates(self.cfg, data or self.data, self.paths)
        write_updates(writes)
        return writes

    def test_renders_both_languages_with_states_and_scope(self):
        updates = prepare_updates(self.cfg, self.data, self.paths)
        self.assertEqual(set(updates), {self.pt, self.en})
        pt, en = updates[self.pt], updates[self.en]
        self.assertIn("[PR #10 · integrado]", pt)
        self.assertIn("[PR #11 · aberto]", pt)
        self.assertIn("[PR #12 · fechado sem integração]", pt)
        self.assertIn("[PR #10 · merged]", en)
        self.assertIn("[PR #11 · open]", en)
        self.assertIn("[PR #12 · closed without merge]", en)
        self.assertIn("5 no total, 2 integrados, 2 abertos", pt)
        self.assertIn("5 total, 2 merged, 2 open", en)
        self.assertIn("23/09/2026", pt)
        self.assertIn("2026-09-23", en)
        self.assertIn("mesmo os não destacados", pt)
        self.assertIn("including those not highlighted", en)
        self.assertIn("Correção de timeout \\| com testes.", pt)
        self.assertIn("Timeout fix \\| with tests.", en)
        self.assertIn("https://github.com/SomeOrg/ProjectOne/pull/10", pt)

    def test_preserves_all_text_outside_markers(self):
        old = {lang: path.read_text(encoding="utf-8") for lang, path in self.paths.items()}
        self._update()
        for language, path in self.paths.items():
            new = path.read_text(encoding="utf-8")
            self.assertEqual(new.split(START)[0], old[language].split(START)[0])
            self.assertEqual(new.split(END)[1], old[language].split(END)[1])
            self.assertEqual(new.count(START), 1)
            self.assertEqual(new.count(END), 1)

    def test_running_twice_and_new_collection_timestamp_do_not_change_files(self):
        self._update()
        previous = {lang: path.read_bytes() for lang, path in self.paths.items()}
        self.assertEqual(prepare_updates(self.cfg, self.data, self.paths), {})
        updated_timestamp = snapshot("2026-09-24T11:00:00Z")
        self.assertEqual(prepare_updates(self.cfg, updated_timestamp, self.paths), {})
        for lang, path in self.paths.items():
            self.assertEqual(path.read_bytes(), previous[lang])
            self.assertNotIn("24/09/2026", path.read_text(encoding="utf-8"))

    def test_status_change_updates_both_languages_and_dates(self):
        self._update()
        updated = snapshot("2026-09-24T11:00:00Z")
        pr = updated["projects"][0]["reference_prs"][1]
        pr.update(status="merged", merged_at="2026-09-24T10:00:00Z")
        updated["projects"][0].update(merged_prs=2, open_prs=1)
        updated["totals"].update(merged_prs=3, open_prs=1)
        updated["latest_merged_at"] = "2026-09-24T10:00:00Z"
        changed = self._update(updated)
        self.assertEqual(set(changed), {self.pt, self.en})
        self.assertIn("PR #11 · integrado", self.pt.read_text(encoding="utf-8"))
        self.assertIn("PR #11 · merged", self.en.read_text(encoding="utf-8"))
        self.assertIn("24/09/2026", self.pt.read_text(encoding="utf-8"))
        self.assertIn("2026-09-24", self.en.read_text(encoding="utf-8"))

    def test_editorial_description_change_is_a_meaningful_update(self):
        self._update()
        revised = copy.deepcopy(self.cfg)
        revised["projects"][0]["pull_requests"][0]["pt"] = "Descrição revisada."
        data = snapshot("2026-09-24T11:00:00Z")
        updates = prepare_updates(revised, data, self.paths)
        self.assertEqual(set(updates), {self.pt})
        self.assertIn("Descrição revisada", updates[self.pt])
        self.assertIn("24/09/2026", updates[self.pt])

    def test_missing_duplicate_reversed_markers_reject_before_any_write(self):
        variants = [
            readme("en").replace(START, ""),
            readme("en").replace(START, START + "\n" + START),
            readme("en").replace(END, "").replace(START, END + "\n" + START),
        ]
        old_pt = self.pt.read_bytes()
        for bad in variants:
            with self.subTest(bad=bad[:75]):
                self.en.write_text(bad, encoding="utf-8")
                old_en = self.en.read_bytes()
                with self.assertRaisesRegex(RenderError, "markers"):
                    self._update()
                self.assertEqual(self.pt.read_bytes(), old_pt)
                self.assertEqual(self.en.read_bytes(), old_en)

    def test_tampered_or_incomplete_snapshot_is_rejected(self):
        cases = []
        def changed(fn):
            result = copy.deepcopy(self.data)
            fn(result)
            cases.append(result)

        changed(lambda s: s.update(repositories=1))
        changed(lambda s: s.update(profile="someone-else"))
        changed(lambda s: s.update(scope="All GitHub PRs"))
        changed(lambda s: s.update(collected_at="2026-09-45T20:00:00Z"))
        changed(lambda s: s["totals"].update(authored_prs=0))
        changed(lambda s: s["projects"][0].update(merged_prs=0))
        changed(lambda s: s["projects"][0].update(repository="rodri-oliveira-dev/Mine"))
        changed(lambda s: s["projects"][0]["reference_prs"].pop())
        changed(lambda s: s["projects"][0]["reference_prs"][0].update(number=999))
        changed(lambda s: s["projects"][0]["reference_prs"][0].update(url="https://example.org"))
        changed(lambda s: s["projects"][0]["reference_prs"][1].update(merged_at="2026-09-01T00:00:00Z"))
        changed(lambda s: s.update(latest_merged_at=None))
        original = {lang: path.read_bytes() for lang, path in self.paths.items()}
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(RenderError):
                    prepare_updates(self.cfg, data, self.paths)
                for lang, path in self.paths.items():
                    self.assertEqual(path.read_bytes(), original[lang])

    def test_write_preserves_original_permissions_and_idempotency(self):
        self.pt.chmod(0o640)
        self.en.chmod(0o600)
        old_modes = {path: stat.S_IMODE(path.stat().st_mode) for path in self.paths.values()}
        self._update()
        for path, old_mode in old_modes.items():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), old_mode)
        self.assertEqual(prepare_updates(self.cfg, self.data, self.paths), {})
        self.assertEqual(self._temporary_files(), [])

    def _temporary_files(self):
        return sorted(path for path in self.root.iterdir()
                      if ".external-contributions-" in path.name)

    def test_second_replace_failure_restores_both_readmes_and_modes(self):
        self.pt.chmod(0o640)
        self.en.chmod(0o600)
        originals = {path: (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
                     for path in self.paths.values()}
        real_replace = os.replace
        calls = []

        def fail_second(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError("injected second replacement failure")
            return real_replace(source, destination)

        with patch("scripts.render_external_contributions.os.replace", side_effect=fail_second):
            with self.assertRaisesRegex(RenderError, "original files rolled back"):
                self._update()
        self.assertEqual(len(calls), 4)  # Two attempts, two restorations.
        for path, (original, mode) in originals.items():
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode)
        self.assertEqual(self._temporary_files(), [])

    def test_keyboard_interrupt_during_second_replace_rolls_back(self):
        originals = {path: path.read_bytes() for path in self.paths.values()}
        real_replace = os.replace
        calls = 0

        def interrupt_second(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return real_replace(source, destination)

        with patch("scripts.render_external_contributions.os.replace",
                   side_effect=interrupt_second):
            with self.assertRaises(KeyboardInterrupt):
                self._update()
        self.assertEqual(calls, 4)
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original)
        self.assertEqual(self._temporary_files(), [])

    def test_rollback_failure_retains_original_backup_for_manual_recovery(self):
        originals = {path: path.read_bytes() for path in self.paths.values()}
        real_replace = os.replace
        calls = 0

        def fail_write_and_rollback(source, destination):
            nonlocal calls
            calls += 1
            if calls in (2, 4):  # English write fails; Portuguese restoration fails.
                raise OSError(f"injected failure {calls}")
            return real_replace(source, destination)

        with patch("scripts.render_external_contributions.os.replace",
                   side_effect=fail_write_and_rollback):
            with self.assertRaisesRegex(RenderError, "manual recovery required") as error:
                self._update()
        self.assertEqual(calls, 4)
        self.assertEqual(self.en.read_bytes(), originals[self.en])
        self.assertNotEqual(self.pt.read_bytes(), originals[self.pt])
        backups = self._temporary_files()
        self.assertEqual(len(backups), 1)
        self.assertIn(".README.md.external-contributions-backup-", backups[0].name)
        self.assertIn(str(backups[0]), str(error.exception))
        self.assertEqual(backups[0].read_bytes(), originals[self.pt])
        os.replace(backups[0], self.pt)
        self.assertEqual(self.pt.read_bytes(), originals[self.pt])
        self.assertEqual(self._temporary_files(), [])

    def test_backup_preparation_failure_keeps_both_originals_untouched(self):
        originals = {path: path.read_bytes() for path in self.paths.values()}
        real_copy = __import__("shutil").copy2
        copies = 0

        def fail_second_backup(source, destination):
            nonlocal copies
            copies += 1
            if copies == 2:
                raise OSError("injected backup failure")
            return real_copy(source, destination)

        with patch("scripts.render_external_contributions.shutil.copy2",
                   side_effect=fail_second_backup):
            with self.assertRaisesRegex(OSError, "injected backup failure"):
                self._update()
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original)
        self.assertEqual(self._temporary_files(), [])

    def test_single_language_update_preserves_other_readme(self):
        self._update()
        unchanged_en = self.en.read_bytes()
        revised = copy.deepcopy(self.cfg)
        revised["projects"][0]["pull_requests"][0]["pt"] = "Descrição revisada."
        updates = prepare_updates(revised, snapshot("2026-09-24T11:00:00Z"), self.paths)
        self.assertEqual(set(updates), {self.pt})
        write_updates(updates)
        self.assertIn("Descrição revisada.", self.pt.read_text(encoding="utf-8"))
        self.assertEqual(self.en.read_bytes(), unchanged_en)
        self.assertEqual(self._temporary_files(), [])

    def test_missing_or_corrupt_snapshot_does_not_modify_readmes(self):
        source = self.root / "snapshot.json"
        editorial = self.root / "config.json"
        editorial.write_text(json.dumps(self.cfg), encoding="utf-8")
        old = {lang: path.read_bytes() for lang, path in self.paths.items()}
        options = [
            "--config", str(editorial),
            "--snapshot", str(source),
            "--readme-pt", str(self.pt),
            "--readme-en", str(self.en),
            "--write",
        ]
        for contents in (None, "{ broken json", json.dumps({"repositories": 0})):
            with self.subTest(contents=contents):
                if contents is None:
                    source.unlink(missing_ok=True)
                else:
                    source.write_text(contents, encoding="utf-8")
                with patch("sys.stderr", new_callable=io.StringIO):
                    self.assertEqual(main(options), 1)
                for lang, path in self.paths.items():
                    self.assertEqual(path.read_bytes(), old[lang])

    def test_cli_dry_run_and_explicit_write(self):
        editorial = self.root / "config.json"
        source = self.root / "snapshot.json"
        editorial.write_text(json.dumps(self.cfg), encoding="utf-8")
        source.write_text(json.dumps(self.data), encoding="utf-8")
        args = [
            "--config", str(editorial), "--snapshot", str(source),
            "--readme-pt", str(self.pt), "--readme-en", str(self.en),
        ]
        before = self.pt.read_bytes()
        with patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main(args), 0)
        self.assertEqual(self.pt.read_bytes(), before)
        with patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main(args + ["--write"]), 0)
        self.assertNotEqual(self.pt.read_bytes(), before)
        after = {lang: path.read_bytes() for lang, path in self.paths.items()}
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(main(args + ["--write"]), 0)
            self.assertIn("Updated: none", output.getvalue())
        for lang, path in self.paths.items():
            self.assertEqual(path.read_bytes(), after[lang])


if __name__ == "__main__":
    unittest.main()
