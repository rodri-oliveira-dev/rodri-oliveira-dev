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


DASHBOARD_TEXT = {
    "pt": {
        "highlights": "Projetos em destaque",
        "work_in_progress": "Acompanhar issues e trabalho em andamento",
        "recent": "Atividade recente",
        "merge_rate": "dos PRs integrados",
        "recent_repo": "Repositório",
        "empty": "Nenhuma contribuição encontrada.",
        "project_link": "Ver repositório",
        "counts": "Contribuições",
        "compact_prs": "PRs",
        "merged_short": "integrados",
        "merged_one": "integrado",
        "open_short": "abertos",
        "open_one": "aberto",
        "closed_short": "fechados sem integração",
        "closed_one": "fechado sem integração",
    },
    "en": {
        "highlights": "Featured projects",
        "work_in_progress": "Track issues and work in progress",
        "recent": "Recent activity",
        "merge_rate": "of PRs merged",
        "recent_repo": "Repository",
        "empty": "No contributions found.",
        "project_link": "View repository",
        "counts": "Contributions",
        "compact_prs": "PRs",
        "merged_short": "merged",
        "merged_one": "merged",
        "open_short": "open",
        "open_one": "open",
        "closed_short": "closed without merge",
        "closed_one": "closed without merge",
    },
}

FEATURED_ORDER = (
    "likec4/likec4",
    "hitmasu/opencnpj",
    "threemammals/ocelot",
    "guibranco/crispywaffle",
)

FEATURED_DESCRIPTIONS = {
    "likec4/likec4": {
        "pt": "Documentação e localização",
        "en": "Documentation and localization",
    },
    "hitmasu/opencnpj": {
        "pt": "Segurança, performance e APIs",
        "en": "Security, performance and APIs",
    },
    "threemammals/ocelot": {
        "pt": "API Gateway e testes",
        "en": "API gateway and testing",
    },
    "guibranco/crispywaffle": {
        "pt": "Serialização de dados",
        "en": "Data serialization",
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


def _featured_projects(projects: list[dict]) -> list[dict]:
    """Favor known projects, then fill any gaps with deterministic data-driven picks."""
    available = {project["repository"].casefold(): project for project in projects}
    selected = [available[name] for name in FEATURED_ORDER if name in available]
    remaining = (project for project in projects if project["repository"].casefold() not in FEATURED_ORDER)
    ranked = sorted(remaining, key=lambda project: (
        -project["totals"]["pull_requests"],
        -project["totals"]["merged"],
        project["repository"].casefold(),
    ))
    return (selected + ranked)[:4]


def _compact_status(value: int, language: str, key: str) -> str:
    ui = DASHBOARD_TEXT[language]
    return f"{value} {ui[key + ('_one' if value == 1 else '_short')]}"


def _pr_count(value: int) -> str:
    return f"{value} {'PR' if value == 1 else 'PRs'}"


def _highlight_card(project: dict | None, language: str) -> tuple[str, str, str]:
    if project is None:
        return ("", "", "")
    repository, counts = project["repository"], project["totals"]
    description = FEATURED_DESCRIPTIONS.get(repository.casefold(), {}).get(language, "")
    return (
        f"**[{_escape(repository)}]({project['url']})**",
        description,
        f"**{_pr_count(counts['pull_requests'])}** · {_compact_status(counts['merged'], language, 'merged')}",
    )


def render_catalog(snapshot: dict, language: str) -> str:
    validate_snapshot(snapshot)
    labels, ui = TEXT[language], DASHBOARD_TEXT[language]
    totals, projects = snapshot["totals"], snapshot["projects"]
    total, merged = totals["pull_requests"], totals["merged"]
    percentage = merged * 100 // total if total else 0
    filled = (merged * 20 + total // 2) // total if total else 0
    meter = chr(96) + "▰" * filled + "▱" * (20 - filled) + chr(96)

    lines = [
        f"# {labels['title']}", "", labels["intro"], "",
        f"- 🌟 [{ui['highlights']}](#featured-projects)",
        f"- 🕒 [{ui['recent']}](#recent-activity)",
        f"- 📚 [{labels['projects']}](#project-index)",
        f"- 📂 [{labels['by_repo']}](#contribution-history)",
        f"- 🛠️ [{ui['work_in_progress']}](https://github.com/users/rodri-oliveira-dev/projects/1/views/1)",
        "", f"## {labels['metrics']}", "",
        f"| {labels['prs']} | {labels['merged']} | {labels['open']} | {labels['repos']} |",
        "| :---: | :---: | :---: | :---: |",
        f"| **{total}** | **{merged}** | **{totals['open']}** | **{totals['repositories']}** |",
        "",
        f"**{percentage}%** {ui['merge_rate']} · {meter} · "
        f"**{totals['closed_unmerged']}** "
        f"{'PR' if totals['closed_unmerged'] == 1 else 'PRs'} "
        f"{ui['closed_one'] if totals['closed_unmerged'] == 1 else ui['closed_short']}",
        "",
        f"**{labels['sync']}:** {_date(snapshot['last_successful_sync'], language)}",
        "", f"_{labels['note']}_", "", "<!-- cspell:disable -->", "",
        '<a id="featured-projects"></a>', "",
        f"## {ui['highlights']}", "",
    ]

    featured = _featured_projects(projects)
    if not featured:
        lines.extend([ui["empty"], ""])
    for start in range(0, len(featured), 2):
        pair = featured[start:start + 2]
        cards = [_highlight_card(project, language) for project in pair]
        if len(cards) == 1:
            cards.append(_highlight_card(None, language))
        lines.extend([
            "| " + " | ".join(card[0] for card in cards) + " |",
            "| --- | --- |",
            "| " + " | ".join(card[1] for card in cards) + " |",
            "| " + " | ".join(card[2] for card in cards) + " |",
            "",
        ])

    lines.extend(['<a id="recent-activity"></a>', "", f"## {ui['recent']}", ""])
    recent = [(project, pr) for project in projects for pr in project["pull_requests"]
              if pr["status"] == "merged"]
    recent.sort(key=lambda item: (
        item[1]["merged_at"], item[0]["repository"].casefold(), item[1]["number"],
    ), reverse=True)
    if recent:
        lines.extend([
            f"| {ui['recent_repo']} | {labels['pr_label']} | {labels['merged_on']} |",
            "| --- | --- | --- |",
        ])
        for project, pr in recent[:5]:
            lines.append(
                f"| [{_escape(project['repository'])}]({project['url']}) | "
                f"[#{pr['number']}]({pr['url']}) — {_escape(pr['title'])} | "
                f"{_date(pr['merged_at'], language)} |"
            )
        lines.append("")
    else:
        lines.extend([ui["empty"], ""])

    lines.extend(['<a id="project-index"></a>', "", f"## {labels['projects']}", ""])
    if projects:
        lines.extend(["| | |", "| --- | --- |"])
        for start in range(0, len(projects), 2):
            pair = projects[start:start + 2]
            cells = [
                f"[{_escape(project['repository'])}](#{_anchor(project['repository'])})"
                for project in pair
            ]
            if len(cells) == 1:
                cells.append("&nbsp;")
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    else:
        lines.extend([ui["empty"], ""])

    lines.extend(['<a id="contribution-history"></a>', "",
                  f"## {labels['by_repo']}", ""])
    if not projects:
        lines.extend([ui["empty"], ""])
    for project in projects:
        repository, counts = project["repository"], project["totals"]
        summary = _pr_count(counts["pull_requests"])
        for status in ("merged", "open", "closed_unmerged"):
            if counts[status]:
                key = "closed" if status == "closed_unmerged" else status
                summary += f" · {_compact_status(counts[status], language, key)}"
        lines.extend([
            f'<a id="{_anchor(repository)}"></a>', "",
            "<details>",
            f"<summary><strong>{repository}</strong> · {summary}</summary>",
            "",
            f"[{ui['project_link']}]({project['url']})", "",
            f"**{labels['total']}:** {counts['pull_requests']} · "
            f"**{labels['merged']}:** {counts['merged']} · "
            f"**{labels['open']}:** {counts['open']} · "
            f"**{labels['closed_unmerged']}:** {counts['closed_unmerged']}", "",
            f"| {labels['pr_label']} | {labels['status_label']} | {labels['opened']} | {labels['merged_on']} |",
            "| --- | --- | --- | --- |",
        ])
        for pr in project["pull_requests"]:
            state = labels["states"][pr["status"]]
            merged_date = _date(pr["merged_at"], language) if pr["merged_at"] else "—"
            lines.append(
                f"| [#{pr['number']}]({pr['url']}) — {_escape(pr['title'])} | "
                f"{state} | {_date(pr['created_at'], language)} | {merged_date} |"
            )
        lines.extend(["", "</details>", ""])
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
