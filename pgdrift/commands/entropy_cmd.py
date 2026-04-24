from __future__ import annotations

import argparse
import json

from pgdrift import audit as audit_mod
from pgdrift import trend as trend_mod
from pgdrift.entropy import compute_entropy


def cmd_entropy(args: argparse.Namespace) -> int:
    """Print schema-change entropy over audit history."""
    records = audit_mod.load_audit(args.config_dir)
    if not records:
        print("No audit records found.")
        return 0

    points = [
        trend_mod._point_from_report(r["report"], r["captured_at"])
        for r in records
        if "report" in r
    ]

    report = compute_entropy(points)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    print(f"Entropy report ({len(report.points)} points)")
    print(f"  Average entropy : {report.average_entropy():.4f}")
    print(f"  Max entropy     : {report.max_entropy():.4f}")
    if report.points:
        for pt in report.points:
            print(f"  {pt.timestamp}  entropy={pt.entropy:.4f}  changes={pt.total_changes}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("entropy", help="Show schema-change entropy over time")
    p.add_argument("--config-dir", default=".", help="Directory for config/audit files")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_entropy)
