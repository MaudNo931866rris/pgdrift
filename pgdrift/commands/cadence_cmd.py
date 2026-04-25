"""CLI command: pgdrift cadence — show schema-change cadence from audit history."""
from __future__ import annotations

import argparse
import json

from pgdrift.audit import list_audits
from pgdrift.cadence import compute_cadence


def cmd_cadence(args: argparse.Namespace) -> int:
    records = list_audits()
    if not records:
        print("No audit records found.")
        return 0

    report = compute_cadence(records)

    if report.is_empty():
        print("Not enough audit records to compute cadence (need at least 2).")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    avg = report.average_interval()
    std = report.stddev_interval()
    regular = report.is_regular()

    print(f"Cadence report ({len(report.entries)} intervals)")
    print(f"  Average interval : {avg:.2f} days")
    print(f"  Std-dev interval : {std:.2f} days")
    print(f"  Regular          : {'yes' if regular else 'no'}")
    print()
    for entry in report.entries:
        print(f"  {entry.captured_at}  profile={entry.profile}  interval={entry.interval_days}d")

    return 0


def register(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("cadence", help="Analyse schema-change cadence from audit history")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_cadence)
