"""CLI command: pgdrift momentum — show schema change momentum over time."""
from __future__ import annotations

import argparse
import json

from pgdrift.audit import load_audit
from pgdrift.trend import _point_from_report
from pgdrift.momentum import compute_momentum


def cmd_momentum(args: argparse.Namespace) -> int:
    records = load_audit()
    if not records:
        print("No audit records found.")
        return 0

    trend_points = []
    for record in records:
        report = record.get("report")
        if report is None:
            continue
        ts = record.get("captured_at", "")
        point = _point_from_report(report, ts)
        trend_points.append(point)

    if not trend_points:
        print("No trend data available.")
        return 0

    momentum = compute_momentum(trend_points)

    if getattr(args, "json", False):
        print(json.dumps(momentum.as_dict(), indent=2))
        return 0

    print(f"Momentum report ({len(momentum.points)} points)")
    print(f"  Average delta : {momentum.average_delta():.2f}")
    if momentum.is_accelerating():
        print("  Trend         : ACCELERATING ▲")
    elif momentum.is_decelerating():
        print("  Trend         : DECELERATING ▼")
    else:
        print("  Trend         : STABLE ─")

    if getattr(args, "verbose", False):
        print()
        for p in momentum.points:
            arrow = {"accelerating": "▲", "decelerating": "▼", "stable": "─"}.get(
                p.direction, " "
            )
            print(f"  {p.timestamp}  changes={p.changes:4d}  delta={p.delta:+4d}  {arrow}")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("momentum", help="Show schema change momentum over time")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--verbose", "-v", action="store_true", help="Show per-point breakdown")
    p.set_defaults(func=cmd_momentum)
