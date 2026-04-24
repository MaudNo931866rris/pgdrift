"""CLI command: pgdrift forecast"""
from __future__ import annotations

import argparse
import json

from pgdrift.config import load
from pgdrift.forecast import build_forecast


def cmd_forecast(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"[error] config file not found: {args.config}")
        return 1

    try:
        cfg.get_profile(args.profile)
    except KeyError:
        print(f"[error] unknown profile: {args.profile}")
        return 1

    report = build_forecast(
        profile=args.profile,
        snapshot_dir=getattr(args, "snapshot_dir", "snapshots"),
        horizons=getattr(args, "horizons", 4),
        window=getattr(args, "window", 3),
    )

    if report.is_empty():
        print("No historical data available to build a forecast.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    print(f"Forecast for profile: {args.profile}")
    print(f"  Based on {len(report.history)} historical data point(s)")
    print()
    print(f"  {'Period':<12} {'Predicted':>10} {'Lower':>10} {'Upper':>10}")
    print("  " + "-" * 46)
    for fp in report.forecast:
        print(
            f"  {fp.period:<12} {fp.predicted_changes:>10.2f}"
            f" {fp.lower_bound:>10.2f} {fp.upper_bound:>10.2f}"
        )
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("forecast", help="Forecast future schema drift")
    p.add_argument("profile", help="Profile name to forecast")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--snapshot-dir", dest="snapshot_dir", default="snapshots")
    p.add_argument("--horizons", type=int, default=4, help="Number of future periods")
    p.add_argument("--window", type=int, default=3, help="Moving-average window size")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_forecast)
