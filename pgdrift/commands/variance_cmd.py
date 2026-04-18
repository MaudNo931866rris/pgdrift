"""CLI command: pgdrift variance — show schema drift variance over time."""
from __future__ import annotations
import argparse
import json
from pgdrift.audit import load_audit
from pgdrift.trend import build_trend_report
from pgdrift.variance import compute_variance


def cmd_variance(args: argparse.Namespace) -> int:
    entries = load_audit(args.dir)
    if not entries:
        print("No audit entries found.")
        return 0

    trend = build_trend_report(entries)
    report = compute_variance(trend)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    print(f"Variance Report  (points: {len(report.points)})")
    print(f"  Stable      : {report.is_stable}")
    print(f"  Max delta   : {report.max_delta}")
    print(f"  Mean changes: {report.mean_changes}")
    print()
    if report.points:
        print(f"  {'Label':<30} {'Changes':>8} {'Delta':>8}")
        print("  " + "-" * 50)
        for p in report.points:
            sign = "+" if p.delta > 0 else ""
            print(f"  {p.label:<30} {p.total_changes:>8} {sign + str(p.delta):>8}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("variance", help="Show schema drift variance over time")
    p.add_argument("--dir", default=".pgdrift/audit", help="Audit directory")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_variance)
