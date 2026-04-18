"""CLI command for detecting stale snapshots."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pgdrift.stale import check_stale

_DEFAULT_DIR = Path(".pgdrift/snapshots")
_DEFAULT_MAX_AGE = 7.0


def cmd_stale(args: argparse.Namespace) -> int:
    snapshot_dir = Path(getattr(args, "snapshot_dir", _DEFAULT_DIR))
    max_age = float(getattr(args, "max_age_days", _DEFAULT_MAX_AGE))

    report = check_stale(snapshot_dir, max_age_days=max_age)

    if not report.entries:
        print("No snapshots found.")
        return 0

    any_stale = False
    for entry in report.entries:
        status = "STALE" if entry.is_stale else "ok"
        print(f"[{status}] {entry.profile} — {entry.snapshot_file} ({entry.age_days}d old)")
        if entry.is_stale:
            any_stale = True

    if any_stale:
        print(f"\nOne or more snapshots exceed the {max_age}-day threshold.", file=sys.stderr)
        return 1

    print("\nAll snapshots are fresh.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("stale", help="Detect stale snapshots")
    p.add_argument("--snapshot-dir", default=str(_DEFAULT_DIR), dest="snapshot_dir")
    p.add_argument("--max-age-days", type=float, default=_DEFAULT_MAX_AGE, dest="max_age_days")
    p.set_defaults(func=cmd_stale)
