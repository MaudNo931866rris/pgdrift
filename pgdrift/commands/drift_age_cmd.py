"""CLI command for drift age reporting."""
from __future__ import annotations

import argparse
import json

from pgdrift.drift_age import compute_drift_age


def cmd_drift_age(args: argparse.Namespace) -> int:
    report = compute_drift_age(args.profile, audit_dir=getattr(args, "audit_dir", None))

    if not report.entries:
        print(f"No drift history found for profile '{args.profile}'.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    print(f"Drift age report for profile: {args.profile}")
    print(f"{'Table':<40} {'First Seen':<26} {'Last Seen':<26} {'Days':>6} {'#':>4}")
    print("-" * 106)
    for entry in report.entries:
        print(
            f"{entry.table:<40} "
            f"{entry.first_seen.isoformat():<26} "
            f"{entry.last_seen.isoformat():<26} "
            f"{entry.age_days:>6.1f} "
            f"{entry.occurrences:>4}"
        )

    oldest = report.oldest()
    if oldest:
        print(f"\nLongest-standing drift: {oldest.table} ({oldest.age_days:.1f} days)")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("drift-age", help="Show how long drift has been present per table")
    p.add_argument("profile", help="Profile name to inspect audit history for")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--audit-dir", default=None, help="Custom audit directory")
    p.set_defaults(func=cmd_drift_age)
