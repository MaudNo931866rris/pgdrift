"""CLI command: pgdrift velocity"""
from __future__ import annotations
import argparse
import json

from pgdrift.velocity import compute_velocity


def cmd_velocity(args: argparse.Namespace) -> int:
    report = compute_velocity(args.snapshot_dir)
    if not report.points:
        print("No audit records found.")
        return 0

    d = report.as_dict()
    if args.json:
        print(json.dumps(d, indent=2))
    else:
        print(f"Average changes/day : {d['average_per_day']}")
        if d["peak"]:
            print(f"Peak                : {d['peak']['changes']} changes on {d['peak']['captured_at']}")
        print(f"Total data points   : {len(d['points'])}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("velocity", help="Show schema drift velocity over time")
    p.add_argument("--snapshot-dir", default=".pgdrift/snapshots", help="Snapshot directory")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_velocity)
