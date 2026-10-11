#!/usr/bin/env python3
"""Validate one structured snapshot and render the PT-BR and English catalogs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    from scripts.external_contributions import REPO_PATTERN, SCOPE, TIMESTAMP_PATTERN
except ModuleNotFoundError:
    from external_contributions import REPO_PATTERN, SCOPE, TIMESTAMP_PATTERN


class RenderError(Exception):
    """Invalid input or failed transactional write."""


TEXT = {
    "pt": {
        "title": "Contribuições open source",
        "intro": "Este catálogo reúne Pull Requests públicos que abri em projetos de terceiros. Os títulos são os originais do GitHub e os estados são reconciliados automaticamente.",
        "metrics": "Indicadores gerais", "projects": "Índice de projetos",
        "by_repo": "Contribuições por repositório", "repos": "Repositórios externos",
        "prs": "PRs encontrados", "merged": "PRs integrados", "open": "PRs abertos",
        "closed_unmerged": "PRs fechados sem integração", "sync": "Última sincronização bem-sucedida",
        "total": "Total", "pr_label": "Pull request", "status_label": "Situação",
        "opened": "Aberto em", "merged_on": "Integrado em",
        "states": {"merged": "Integrado", "open": "Aberto", "closed_unmerged": "Fechado sem integração"},
        "date": "%d/%m/%Y", "note": "A data acima corresponde à sincronização que produziu a versão publicada atual; consultas sem mudança factual não geram commit.",
    },
    "en": {
        "title": "Open-source contributions",
        "intro": "This catalog lists public pull requests I opened in third-party projects. Titles remain exactly as provided by GitHub, while statuses are reconciled automatically.",
        "metrics": "General indicators", "projects": "Project index",
        "by_repo": "Contributions by repository", "repos": "External repositories",
        "prs": "PRs found", "merged": "Merged PRs", "open": "Open PRs",
        "closed_unmerged": "PRs closed without merge", "sync": "Last successful synchronization",
        "total": "Total", "pr_label": "Pull request", "status_label": "Status",
        "opened": "Opened", "merged_on": "Merged",
        "states": {"merged": "Merged", "open": "Open", "closed_unmerged": "Closed without merge"},
        "date": "%Y-%m-%d", "note": "The date above is the synchronization that produced the current published version; queries with no factual changes create no commit.",
    },
}


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not TIMESTAMP_PATTERN.fullmatch(value):
        raise RenderError("Snapshot contains an invalid UTC timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise RenderError("Snapshot contains an invalid date") from error


def validate_snapshot(value: object) -> dict:
    if (not isinstance(value, dict) or value.get("schema_version") != 2
            or value.get("scope") != SCOPE or not isinstance(value.get("profile"), str)):
        raise RenderError("Snapshot schema, scope, or profile is invalid")
    _timestamp(value.get("last_successful_sync"))
    totals, projects = value.get("totals"), value.get("projects")
    keys = ("repositories", "pull_requests", "merged", "open", "closed_unmerged")
    if (not isinstance(totals, dict) or any(type(totals.get(k)) is not int or totals[k] < 0 for k in keys)
            or not isinstance(projects, list) or totals["repositories"] != len(projects)):
        raise RenderError("Snapshot totals are invalid")
    aggregate = {key: 0 for key in keys[1:]}
    identities: set[int] = set()
    keys_seen: set[tuple[str, int]] = set()
    prior_project_key = None
    for project in projects:
        if not isinstance(project, dict):
            raise RenderError("Snapshot project is invalid")
        repository, url, activity = project.get("repository"), project.get("url"), project.get("activity_at")
        if (not isinstance(repository, str) or not REPO_PATTERN.fullmatch(repository)
                or url != f"https://github.com/{repository}"):
            raise RenderError("Snapshot repository identity or URL is invalid")
        activity_dt = _timestamp(activity)
        project_key = (activity_dt, repository.casefold())
        if prior_project_key is not None and (activity_dt > prior_project_key[0]
                or (activity_dt == prior_project_key[0] and repository.casefold() < prior_project_key[1])):
            raise RenderError("Snapshot projects are not deterministically ordered")
        prior_project_key = project_key
        prs, counts = project.get("pull_requests"), project.get("totals")
        if not isinstance(prs, list) or not isinstance(counts, dict):
            raise RenderError("Snapshot project contents are invalid")
        actual = {state: 0 for state in ("merged", "open", "closed_unmerged")}
        previous_pr_key = None
        for pr in prs:
            if not isinstance(pr, dict):
                raise RenderError("Snapshot PR is invalid")
            number, identifier, status = pr.get("number"), pr.get("id"), pr.get("status")
            if (type(number) is not int or number < 1 or type(identifier) is not int or identifier < 1
                    or identifier in identities or status not in actual
                    or pr.get("url") != f"https://github.com/{repository}/pull/{number}"):
                raise RenderError("Snapshot contains an invalid or duplicate PR identity")
            title = pr.get("title")
            if not isinstance(title, str) or not title.strip() or any(c in title for c in "\r\n\x00"):
                raise RenderError("Snapshot contains an invalid PR title")
            created = _timestamp(pr.get("created_at"))
            updated = _timestamp(pr.get("updated_at"))
            merged_at = pr.get("merged_at")
            if status == "merged":
                _timestamp(merged_at)
            elif merged_at is not None:
                raise RenderError("Unmerged PR has a merge timestamp")
            order_key = (created, number)
            if previous_pr_key is not None and order_key > previous_pr_key:
                raise RenderError("Snapshot PRs are not deterministically ordered")
            previous_pr_key = order_key
            identities.add(identifier)
            keys_seen.add((repository.casefold(), number))
            actual[status] += 1
            if updated > activity_dt:
                raise RenderError("Project activity precedes PR activity")
        expected = {"pull_requests": len(prs), **actual}
        if counts != expected:
            raise RenderError("Per-project totals are inconsistent")
        for key, count in expected.items():
            aggregate[key] += count
    if len(keys_seen) != totals["pull_requests"] or aggregate != {k: totals[k] for k in aggregate}:
        raise RenderError("Aggregate totals are inconsistent")
    return value


def load_snapshot(path: Path) -> dict:
    try:
        return validate_snapshot(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError) as error:
        raise RenderError("Snapshot could not be read") from error


def _escape(value: str) -> str:
    replacements = (("\\", r"\\"), ("`", r"\`"), ("*", r"\*"), ("_", r"\_"),
                    ("[", r"\["), ("]", r"\]"), ("<", "&lt;"), (">", "&gt;"), ("|", r"\|"))
    for old, new in replacements:
        value = value.replace(old, new)
    return value


def _anchor(repository: str) -> str:
    # Repository names are case-insensitive. Encoding every UTF-8 byte preserves
    # punctuation identity, so names such as owner/a.b and owner/a-b cannot collide.
    return "repository-" + repository.casefold().encode("utf-8").hex()


def _date(value: str, language: str) -> str:
    return _timestamp(value).strftime(TEXT[language]["date"])


def render_catalog(snapshot: dict, language: str) -> str:
    validate_snapshot(snapshot)
    labels = TEXT[language]
    totals = snapshot["totals"]
    lines = [f"# {labels['title']}", "", labels["intro"], "", f"## {labels['metrics']}", "",
             f"- **{labels['repos']}:** {totals['repositories']}",
             f"- **{labels['prs']}:** {totals['pull_requests']}",
             f"- **{labels['merged']}:** {totals['merged']}",
             f"- **{labels['open']}:** {totals['open']}",
             f"- **{labels['closed_unmerged']}:** {totals['closed_unmerged']}",
             f"- **{labels['sync']}:** {_date(snapshot['last_successful_sync'], language)}", "",
             f"_{labels['note']}_", "", f"## {labels['projects']}", "",
             "<!-- cspell:disable -->"]
    for project in snapshot["projects"]:
        repository = project["repository"]
        lines.append(f"- [{_escape(repository)}](#{_anchor(repository)})")
    lines.extend(["", f"## {labels['by_repo']}", ""])
    for project in snapshot["projects"]:
        repository, counts = project["repository"], project["totals"]
        lines.extend([f'<a id="{_anchor(repository)}"></a>', "",
                      f"### [{_escape(repository)}]({project['url']})", "",
                      f"**{labels['total']}:** {counts['pull_requests']} · **{labels['merged']}:** {counts['merged']} · **{labels['open']}:** {counts['open']} · **{labels['closed_unmerged']}:** {counts['closed_unmerged']}", ""])
        lines.extend([f"| {labels['pr_label']} | {labels['status_label']} | {labels['opened']} | {labels['merged_on']} |",
                      "| --- | --- | --- | --- |"])
        for pr in project["pull_requests"]:
            state = labels["states"][pr["status"]]
            merged_date = _date(pr["merged_at"], language) if pr["merged_at"] else "—"
            lines.append(f"| [#{pr['number']}]({pr['url']}) — {_escape(pr['title'])} | {state} | {_date(pr['created_at'], language)} | {merged_date} |")
        lines.append("")
    lines.append("<!-- cspell:enable -->")
    return "\n".join(lines).rstrip() + "\n"


def prepare_updates(snapshot: dict, paths: dict[str, Path]) -> dict[Path, str]:
    validate_snapshot(snapshot)
    if set(paths) != set(TEXT) or len(set(paths.values())) != 2:
        raise RenderError("Two distinct PT-BR and English output paths are required")
    return {paths[language]: render_catalog(snapshot, language) for language in ("pt", "en")}


def write_updates(updates: dict[Path, str]) -> None:
    staged, backups, attempted, retained = {}, {}, [], set()
    try:
        for path, content in updates.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                             prefix=f".{path.name}.stage-", delete=False) as handle:
                handle.write(content)
                staged[path] = Path(handle.name)
            os.chmod(staged[path], mode)
            if path.exists():
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.backup-", delete=False) as handle:
                    backups[path] = Path(handle.name)
                shutil.copy2(path, backups[path])
        for path in updates:
            attempted.append(path)
            os.replace(staged[path], path)
        for backup in backups.values():
            backup.unlink(missing_ok=True)
    except OSError as error:
        failed = []
        for path in reversed(attempted):
            try:
                if path in backups:
                    os.replace(backups[path], path)
                else:
                    path.unlink(missing_ok=True)
            except OSError:
                recovery = backups.get(path, path)
                failed.append(str(recovery))
                retained.add(recovery)
        detail = f"; preserved backups: {', '.join(failed)}" if failed else ""
        raise RenderError("Catalog write failed and rollback was attempted" + detail) from error
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
        for backup in backups.values():
            if backup not in retained:
                backup.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output-pt", type=Path, default=Path("docs/open-source-contributions.md"))
    parser.add_argument("--output-en", type=Path, default=Path("docs/open-source-contributions.en.md"))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        updates = prepare_updates(load_snapshot(args.snapshot), {"pt": args.output_pt, "en": args.output_en})
        changed = [str(path) for path, content in updates.items()
                   if not path.exists() or path.read_text(encoding="utf-8") != content]
        if args.write:
            write_updates(updates)
    except (RenderError, OSError) as error:
        print(f"Rendering failed: {error}", file=sys.stderr)
        return 1
    print("Changed catalogs: " + (", ".join(changed) if changed else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
