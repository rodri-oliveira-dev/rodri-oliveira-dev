#!/usr/bin/env python3
"""Prepare an honest optional-discovery report for a curated README preview."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

UNAVAILABLE = {
    "schema_version": 1,
    "status": "unavailable",
    "reason": "Optional external discovery did not complete; candidate count is unknown.",
}


def prepare_report(discovery_result: str, source: Path) -> dict:
    """Pass through valid success data or clearly identify unavailable discovery.

    A failed optional job must never be represented as zero new repositories.
    A supposedly successful job missing its report is a hard error.
    """
    if discovery_result != "success":
        return dict(UNAVAILABLE)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Successful discovery has no valid candidate report") from error
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 1
        or not isinstance(payload.get("candidate_repositories"), list)
        or payload.get("status") == "unavailable"
    ):
        raise ValueError("Successful discovery returned malformed candidate data")
    return payload


def main(argv: list[str] | None = None) -> int:
    """Write discovery status in the temporary preview directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovery-result", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = prepare_report(args.discovery_result, args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + ".tmp")
        try:
            temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, args.output)
        finally:
            temporary.unlink(missing_ok=True)
    except (ValueError, OSError) as error:
        print(f"Unable to prepare discovery report: {error}", file=sys.stderr)
        return 1
    print("Discovery unavailable" if report.get("status") == "unavailable" else "Discovery report verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
