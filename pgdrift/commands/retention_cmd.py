"""CLI commands for managing retention policies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pgdrift.audit import list_audits
from pgdrift.retention import (
    RetentionPolicy,
    evaluate_retention,
    load_retention,
    save_retention,
)
from pgdrift.snapshot import load_snapshot

_SNAPSHOT_DIR = Path(".pgdrift/snapshots")
_AUDIT_DIR = Path(".pgdrift/audit")
_RETENTION_DIR = Path(".pgdrift")


def cmd_retention_set(args: argparse.Namespace) -> int:
    policy = RetentionPolicy(
        max_snapshot_days=args.snapshot_days,
        max_audit_days=args.audit_days,
    )
    save_retention(_RETENTION_DIR, policy)
    print(
        f"Retention policy saved: snapshots={args.snapshot_days}d, "
        f"audit={args.audit_days}d"
    )
    return 0


def cmd_retention_show(args: argparse.Namespace) -> int:
    policy = load_retention(_RETENTION_DIR)
    print(json.dumps({
        "max_snapshot_days": policy.max_snapshot_days,
        "max_audit_days": policy.max_audit_days,
    }, indent=2))
    return 0


def cmd_retention_check(args: argparse.Namespace) -> int:
    policy = load_retention(_RETENTION_DIR)

    snapshots: list = []
    if _SNAPSHOT_DIR.exists():
        for f in _SNAPSHOT_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                data.setdefault("name", f.stem)
                snapshots.append(data)
            except Exception:
                pass

    audits = list_audits(_AUDIT_DIR) if _AUDIT_DIR.exists() else []

    report = evaluate_retention(policy, snapshots, audits)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 1 if report.any_violations() else 0

    if not report.any_violations():
        print("All snapshots and audit records are within retention policy.")
        return 0

    print(f"Retention violations ({len(report.violations)}):")
    for v in report.violations:
        print(f"  [{v.kind}] {v.name}  age={v.age_days}d  captured={v.captured_at}")
    return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("retention", help="Manage data retention policies")
    sub = p.add_subparsers(dest="retention_cmd")

    p_set = sub.add_parser("set", help="Set retention policy")
    p_set.add_argument("--snapshot-days", type=int, default=90)
    p_set.add_argument("--audit-days", type=int, default=180)
    p_set.set_defaults(func=cmd_retention_set)

    p_show = sub.add_parser("show", help="Show current retention policy")
    p_show.set_defaults(func=cmd_retention_show)

    p_check = sub.add_parser("check", help="Check for retention violations")
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=cmd_retention_check)
