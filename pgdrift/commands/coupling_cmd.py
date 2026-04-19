"""CLI command for schema coupling analysis."""
from __future__ import annotations
import argparse
import json
from pgdrift.coupling import compute_coupling


def cmd_coupling(args: argparse.Namespace) -> int:
    report = compute_coupling(
        audit_dir=getattr(args, "audit_dir", ".pgdrift/audit"),
        min_co_changes=getattr(args, "min_co_changes", 2),
    )

    if not report.has_coupling():
        print("No table coupling detected.")
        return 0

    threshold = getattr(args, "threshold", 0.0)
    pairs = report.strong_pairs(threshold) if threshold > 0 else report.pairs

    if not pairs:
        print(f"No pairs meet coupling threshold {threshold}.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps([p.as_dict() for p in pairs], indent=2))
        return 0

    print(f"{'Table A':<30} {'Table B':<30} {'Co-changes':>10} {'Ratio':>8}")
    print("-" * 82)
    for p in pairs:
        print(f"{p.table_a:<30} {p.table_b:<30} {p.co_changes:>10} {p.coupling_ratio():>8.2f}")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("coupling", help="Show co-changing table pairs from audit history")
    p.add_argument("--audit-dir", default=".pgdrift/audit", help="Path to audit directory")
    p.add_argument("--min-co-changes", type=int, default=2, help="Minimum co-change count")
    p.add_argument("--threshold", type=float, default=0.0, help="Minimum coupling ratio to show")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_coupling)
