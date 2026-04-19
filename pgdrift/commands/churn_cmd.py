"""CLI command for schema churn analysis."""
from __future__ import annotations
import argparse
import json
from pgdrift.churn import compute_churn
from pgdrift.config import load


def cmd_churn(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        return 1

    try:
        cfg.get_profile(args.profile)
    except KeyError:
        print(f"Unknown profile: {args.profile}")
        return 1

    report = compute_churn(args.profile)
    top_n = getattr(args, "top", 10)
    churned = report.most_churned(top_n)

    if not churned:
        print("No churn data found.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    print(f"{'Table':<40} {'Changes':>8} {'First Seen':<22} {'Last Seen':<22}")
    print("-" * 94)
    for entry in churned:
        print(f"{entry.table:<40} {entry.change_count:>8} {entry.first_seen:<22} {entry.last_seen:<22}")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("churn", help="Show schema churn (most frequently changed tables)")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--profile", required=True, help="Profile name")
    p.add_argument("--top", type=int, default=10, help="Number of top entries to show")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_churn)
