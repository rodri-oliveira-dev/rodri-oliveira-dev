#!/usr/bin/env python3
"""Render selected third-party contributions in both profile READMEs.

The editorial descriptions live exclusively in the curated JSON configuration.
The authenticated collector produces the complete, validated JSON snapshot.
No network calls or credentials are needed by this renderer.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    from scripts.external_contributions import CollectionError, load_config
except ModuleNotFoundError:
    # Permit invoking this file as python3 scripts/render_external_contributions.py.
    from external_contributions import CollectionError, load_config


START = "<!-- EXTERNAL_CONTRIBUTIONS:START -->"
END = "<!-- EXTERNAL_CONTRIBUTIONS:END -->"
SCOPE = "Public PRs authored by this profile in the curated external repositories only"
LANGUAGES = {
    "pt": {
        "header": "| Projeto externo | Colaboração e PRs de referência |\n| --- | --- |",
        "states": {"merged": "integrado", "open": "aberto", "closed_unmerged": "fechado sem integração"},
        "summary": (
            "**PRs públicos de minha autoria nos {repos} projetos externos selecionados:** "
            "{authored} no total, {merged} integrados, {opened} abertos e "
            "{closed} fechados sem integração. **Projetos com PRs integrados:** {with_merged}."
        ),
        "note": (
            "*A seleção e as descrições são editoriais. Os números incluem todos os PRs "
            "públicos de minha autoria nesses projetos, mesmo os não destacados na tabela. "
            "Atualização do painel: {date}.*"
        ),
        "date_pattern": re.compile(r"Atualização do painel: (\d{2}/\d{2}/\d{4})\.\*$"),
    },
    "en": {
        "header": "| External project | Contributions and reference PRs |\n| --- | --- |",
        "states": {"merged": "merged", "open": "open", "closed_unmerged": "closed without merge"},
        "summary": (
            "**Public PRs authored by me in the {repos} selected external projects:** "
            "{authored} total, {merged} merged, {opened} open and "
            "{closed} closed without merge. **Projects with merged PRs:** {with_merged}."
        ),
        "note": (
            "*Project selection and descriptions are editorial. Figures include all public "
            "PRs I authored in these projects, including those not highlighted in the table. "
            "Dashboard updated: {date}.*"
        ),
        "date_pattern": re.compile(r"Dashboard updated: (\d{4}-\d{2}-\d{2})\.\*$"),
    },
}


class RenderError(Exception):
    """Invalid inputs or README markers; no README should be changed."""


def _positive_int(value: object, *, allow_zero: bool = True) -> bool:
    return type(value) is int and (value >= 0 if allow_zero else value > 0)


def _utc_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ):
        raise RenderError("Snapshot contains an invalid UTC collection timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise RenderError("Snapshot collection timestamp is not a valid date") from error


def _validated_snapshot(config: dict, snapshot: object) -> dict:
    """Reject partial, altered, or out-of-scope data before touching a README."""
    if not isinstance(snapshot, dict):
        raise RenderError("Snapshot must be an object")
    if (
        snapshot.get("schema_version") != 1
        or snapshot.get("profile") != config["profile"]
        or snapshot.get("scope") != SCOPE
        or snapshot.get("repositories") != len(config["projects"])
    ):
        raise RenderError("Snapshot schema, scope or profile does not match curators")
    _utc_timestamp(snapshot.get("collected_at"))
    totals, projects = snapshot.get("totals"), snapshot.get("projects")
    keys = (
        "authored_prs",
        "merged_prs",
        "open_prs",
        "closed_unmerged_prs",
        "repositories_with_merged_prs",
    )
    if (
        not isinstance(totals, dict)
        or any(not _positive_int(totals.get(key)) for key in keys)
        or not isinstance(projects, list)
        or len(projects) != len(config["projects"])
    ):
        raise RenderError("Snapshot totals or project count are invalid")

    sums = dict.fromkeys(keys, 0)
    for curated, project in zip(config["projects"], projects):
        if not isinstance(project, dict) or project.get("repository") != curated["repository"]:
            raise RenderError("Snapshot project ordering/scope does not match the curation")
        for key in keys[:-1]:
            if not _positive_int(project.get(key)):
                raise RenderError("Invalid per-project PR count")
            sums[key] += project[key]
        if project["authored_prs"] != sum(project[key] for key in keys[1:4]):
            raise RenderError("Inconsistent per-project PR totals")
        sums["repositories_with_merged_prs"] += int(project["merged_prs"] > 0)

        references = project.get("reference_prs")
        curated_references = curated["pull_requests"]
        if not isinstance(references, list) or len(references) != len(curated_references):
            raise RenderError("Missing or extra curated reference PR")
        seen = set()
        state_counts = dict.fromkeys(("merged", "open", "closed_unmerged"), 0)
        for reference, editorial in zip(references, curated_references):
            number = editorial["number"]
            expected_url = f"https://github.com/{curated['repository']}/pull/{number}"
            if (
                not isinstance(reference, dict)
                or reference.get("number") != number
                or number in seen
                or reference.get("url") != expected_url
                or reference.get("status") not in state_counts
            ):
                raise RenderError("Reference PR does not match the editorial source")
            seen.add(number)
            status, merged_at = reference["status"], reference.get("merged_at")
            if status == "merged":
                _utc_timestamp(merged_at)
            elif merged_at is not None:
                raise RenderError("An open or unmerged PR cannot have a merge timestamp")
            state_counts[status] += 1
        for status, key in (("merged", "merged_prs"), ("open", "open_prs"), ("closed_unmerged", "closed_unmerged_prs")):
            if state_counts[status] > project[key]:
                raise RenderError("Reference PR states exceed the project totals")

    if any(sums[key] != totals[key] for key in keys):
        raise RenderError("Snapshot aggregate totals do not match curated projects")
    if totals["authored_prs"] != sum(totals[key] for key in keys[1:4]):
        raise RenderError("Snapshot PR counts are inconsistent")
    latest = snapshot.get("latest_merged_at")
    if latest is not None:
        _utc_timestamp(latest)
    if bool(latest) != bool(totals["merged_prs"]):
        raise RenderError("Last merge timestamp disagrees with merged PR totals")
    return snapshot


def load_snapshot(path: Path, config: dict) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RenderError("Snapshot not found or invalid; no README was changed") from error
    return _validated_snapshot(config, payload)


def _inline(value: object, *, project_name: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or any(
        char in value for char in ("\n", "\r", "\x00")
    ):
        raise RenderError("Editorial text is empty or contains a newline/control character")
    result = value.replace("|", r"\|")
    # Project labels are plain text, while trusted editorial descriptions may use Markdown.
    if project_name:
        result = result.replace("\\", r"\\").replace("[", r"\[").replace("]", r"\]")
    return result


def _date(snapshot: dict, language: str) -> str:
    parsed = _utc_timestamp(snapshot["collected_at"])
    return parsed.strftime("%d/%m/%Y" if language == "pt" else "%Y-%m-%d")


def render_block(config: dict, snapshot: dict, language: str, date_override: str | None = None) -> str:
    labels = LANGUAGES[language]
    totals = snapshot["totals"]
    summary = labels["summary"].format(
        repos=snapshot["repositories"],
        authored=totals["authored_prs"],
        merged=totals["merged_prs"],
        opened=totals["open_prs"],
        closed=totals["closed_unmerged_prs"],
        with_merged=totals["repositories_with_merged_prs"],
    )
    rows = []
    for curated, computed in zip(config["projects"], snapshot["projects"]):
        repository = curated["repository"]
        project_label = _inline(curated["name"], project_name=True)
        descriptions = []
        for editorial, reference in zip(curated["pull_requests"], computed["reference_prs"]):
            number, state = editorial["number"], reference["status"]
            label = labels["states"][state]
            description = _inline(editorial[language])
            # URL comes from the validated curation, never from a GitHub response.
            url = f"https://github.com/{repository}/pull/{number}"
            descriptions.append(f"[PR #{number} · {label}]({url}): {description}")
        rows.append(
            f"| **[{project_label}](https://github.com/{repository})** | "
            + "<br><br>".join(descriptions) + " |"
        )
    updated = date_override if date_override is not None else _date(snapshot, language)
    note = labels["note"].format(date=updated)
    return "\n\n".join((summary, labels["header"] + "\n" + "\n".join(rows), note))


def replace_block(original: str, generated: str, language: str, snapshot: dict) -> str:
    if original.count(START) != 1 or original.count(END) != 1:
        raise RenderError(f"README {language}: missing or duplicate contribution markers")
    start, end = original.index(START), original.index(END)
    if start >= end:
        raise RenderError(f"README {language}: contribution markers are out of order")
    prefix = original[:start + len(START)]
    suffix = original[end:]
    previous = original[start + len(START):end].strip("\n")
    # Ignore only the date displayed by this renderer: the collector changes its
    # collected_at on every run, but unchanged statuses/totals/descriptions should
    # not generate README churn.
    match = LANGUAGES[language]["date_pattern"].search(previous)
    if match:
        prior_date = match.group(1)
        if previous == render_block_from_date(generated, language, snapshot, prior_date):
            return original
    return prefix + "\n\n" + generated + "\n\n" + suffix


def render_block_from_date(generated: str, language: str, snapshot: dict, prior_date: str) -> str:
    current = _date(snapshot, language)
    pattern = LANGUAGES[language]["date_pattern"]
    if not pattern.search(generated):
        raise RenderError("Generated Markdown does not contain the expected update date")
    # Change only the final update date, never dates inside PR descriptions.
    return pattern.sub(lambda m: m.group(0).replace(current, prior_date), generated)


def prepare_updates(config: dict, snapshot: dict, paths: dict[str, Path]) -> dict[Path, str]:
    """Prepare BOTH README files in memory; no partial write on bad inputs."""
    _validated_snapshot(config, snapshot)
    if len(set(paths.values())) != 2 or set(paths) != set(LANGUAGES):
        raise RenderError("Two distinct README paths are required")
    updates = {}
    for language, path in paths.items():
        try:
            original = path.read_text(encoding="utf-8")
        except OSError as error:
            raise RenderError(f"README {language} could not be read") from error
        generated = render_block(config, snapshot, language)
        replacement = replace_block(original, generated, language, snapshot)
        if replacement != original:
            updates[path] = replacement
    return updates


def write_updates(updates: dict[Path, str]) -> None:
    """Stage both versions and retain original backups until all replacements succeed.

    os.replace is atomic for a single path, not across multiple README files.
    A failed replacement triggers best-effort rollback of every attempted path.
    Failed rollback backups are retained for explicit manual recovery.
    """
    staging: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    attempted: list[Path] = []
    retained: set[Path] = set()
    try:
        # Complete all staging and backups before modifying either original.
        for path, content in updates.items():
            original_mode = stat.S_IMODE(path.stat().st_mode)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=path.parent,
                prefix=f".{path.name}.external-contributions-stage-", delete=False
            ) as destination:
                staging[path] = Path(destination.name)
                destination.write(content)
            os.chmod(staging[path], original_mode)
            with tempfile.NamedTemporaryFile(
                dir=path.parent,
                prefix=f".{path.name}.external-contributions-backup-", delete=False
            ) as destination:
                backups[path] = Path(destination.name)
            shutil.copy2(path, backups[path])

        try:
            for path, temporary in staging.items():
                # Include the failing path: an injected failure may occur after
                # the filesystem has already completed the replacement.
                attempted.append(path)
                os.replace(temporary, path)
        except BaseException as error:
            # KeyboardInterrupt and SystemExit also need rollback before
            # propagating; otherwise finally would discard their backups.
            recovery_errors = []
            for path in reversed(attempted):
                try:
                    os.replace(backups[path], path)
                except OSError as rollback_error:
                    retained.add(backups[path])
                    recovery_errors.append(
                        f"{path}: {rollback_error}; original backup: {backups[path]}"
                    )
            if recovery_errors:
                raise RenderError(
                    f"README update failed ({error}); manual recovery required: "
                    + "; ".join(recovery_errors)
                ) from error
            if isinstance(error, OSError):
                raise RenderError(
                    f"README update failed ({error}); original files rolled back"
                ) from error
            raise
    finally:
        for temporary in staging.values():
            temporary.unlink(missing_ok=True)
        for backup in backups.values():
            if backup not in retained:
                backup.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(".github/external-contributions.json"))
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--readme-pt", type=Path, default=Path("README.md"))
    parser.add_argument("--readme-en", type=Path, default=Path("README.en.md"))
    parser.add_argument("--write", action="store_true", help="Update READMEs; default is a dry run")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        snapshot = load_snapshot(args.snapshot, config)
        updates = prepare_updates(
            config, snapshot, {"pt": args.readme_pt, "en": args.readme_en}
        )
        if args.write:
            write_updates(updates)
    except (CollectionError, RenderError, OSError) as error:
        print(f"Rendering failed: {error}", file=sys.stderr)
        return 1
    changed = ", ".join(str(path) for path in updates) or "none"
    print(f"{'Updated' if args.write else 'Would update'}: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
