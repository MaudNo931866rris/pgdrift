"""CLI commands for managing and evaluating drift policies."""
from __future__ import annotations

import sys
from pathlib import Path

from pgdrift.policy import (
    PolicyRule, save_policy, load_policy, list_policies,
    delete_policy, evaluate_policy,
)

_DEFAULT_BASE = Path(".pgdrift/policies")


def cmd_policy_save(args) -> int:
    base = Path(getattr(args, "policy_dir", _DEFAULT_BASE))
    rule = PolicyRule(
        name=args.name,
        max_added_tables=args.max_added,
        max_removed_tables=args.max_removed,
        max_modified_tables=args.max_modified,
        allow_destructive=not args.no_destructive,
    )
    save_policy(rule, base)
    print(f"Policy '{args.name}' saved.")
    return 0


def cmd_policy_list(args) -> int:
    base = Path(getattr(args, "policy_dir", _DEFAULT_BASE))
    names = list_policies(base)
    if not names:
        print("No policies defined.")
    for n in names:
        print(n)
    return 0


def cmd_policy_delete(args) -> int:
    base = Path(getattr(args, "policy_dir", _DEFAULT_BASE))
    if delete_policy(args.name, base):
        print(f"Policy '{args.name}' deleted.")
        return 0
    print(f"Policy '{args.name}' not found.", file=sys.stderr)
    return 1


def cmd_policy_check(args) -> int:
    """Evaluate a named policy against a live diff."""
    from pgdrift.config import load as load_config, get_profile
    from pgdrift.inspector import fetch_schema
    from pgdrift.diff import compute_drift
    import psycopg2

    base = Path(getattr(args, "policy_dir", _DEFAULT_BASE))
    rule = load_policy(args.name, base)
    if rule is None:
        print(f"Policy '{args.name}' not found.", file=sys.stderr)
        return 1

    cfg = load_config(args.config)
    if cfg is None:
        print("Config not found.", file=sys.stderr)
        return 1

    src = get_profile(cfg, args.source)
    tgt = get_profile(cfg, args.target)
    if src is None or tgt is None:
        print("Unknown profile.", file=sys.stderr)
        return 1

    with psycopg2.connect(src.dsn) as c1, psycopg2.connect(tgt.dsn) as c2:
        source_tables = fetch_schema(c1)
        target_tables = fetch_schema(c2)

    report = compute_drift(args.source, args.target, source_tables, target_tables)
    result = evaluate_policy(rule, report)

    if result.passed:
        print(f"Policy '{rule.name}' PASSED.")
        return 0
    for v in result.violations:
        print(f"VIOLATION: {v.message}", file=sys.stderr)
    return 1


def register(subparsers):
    p = subparsers.add_parser("policy", help="Manage drift policies")
    sub = p.add_subparsers(dest="policy_cmd")

    ps = sub.add_parser("save")
    ps.add_argument("name")
    ps.add_argument("--max-added", type=int, default=None, dest="max_added")
    ps.add_argument("--max-removed", type=int, default=None, dest="max_removed")
    ps.add_argument("--max-modified", type=int, default=None, dest="max_modified")
    ps.add_argument("--no-destructive", action="store_true")
    ps.set_defaults(func=cmd_policy_save)

    pl = sub.add_parser("list")
    pl.set_defaults(func=cmd_policy_list)

    pd = sub.add_parser("delete")
    pd.add_argument("name")
    pd.set_defaults(func=cmd_policy_delete)

    pc = sub.add_parser("check")
    pc.add_argument("name")
    pc.add_argument("--config", default="pgdrift.yml")
    pc.add_argument("--source", required=True)
    pc.add_argument("--target", required=True)
    pc.set_defaults(func=cmd_policy_check)
