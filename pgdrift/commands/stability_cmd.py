"""CLI command: pgdrift stability."""
from __future__ import annotations

import argparse
import json

from pgdrift.stability import compute_stability


def cmd_stability(args: argparse.Namespace) -> int:
    report = compute_stability(getattr(args, "snapshot_dir", None))

    if not report.entries:
        print("No audit records found – stability data unavailable.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    top_n = getattr(args, "top", 10)
    print(f"Schema Stability Report  (avg score: {report.average_score():.4f})")
    print(f"{'Table':<40} {'Changes':>8} {'Snapshots':>10} {'Score':>8}")
    print("-" * 70)

    entries = sorted(report.entries, key=lambda e: e.stability_score)
    for entry in entries[:top_n]:
        bar = "#" * int((1.0 - entry.stability_score) * 20)
        print(
            f"{entry.table:<40} {entry.change_count:>8} "
            f"{entry.snapshot_count:>10} {entry.stability_score:>8.4f}  {bar}"
        )
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "stability",
        help="Show per-table schema stability scores derived from audit history.",
    )
    p.add_argument(
        "--snapshot-dir",
        dest="snapshot_dir",
        default=None,
        help="Override the snapshot directory.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of least-stable tables to display (default: 10).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON.",
    )
    p.set_defaults(func=cmd_stability)
