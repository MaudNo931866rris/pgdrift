"""CLI sub-commands for managing column redaction rules."""

from __future__ import annotations

import argparse
from pathlib import Path

from pgdrift import redact as redact_module


def cmd_redact_add(args: argparse.Namespace) -> int:
    config_dir = Path(args.config_dir) if hasattr(args, "config_dir") and args.config_dir else Path(".")
    redact_module.add_redact_rule(config_dir, args.table, args.column)
    print(f"Redact rule added: {args.table}.{args.column}")
    return 0


def cmd_redact_remove(args: argparse.Namespace) -> int:
    config_dir = Path(args.config_dir) if hasattr(args, "config_dir") and args.config_dir else Path(".")
    removed = redact_module.remove_redact_rule(config_dir, args.table, args.column)
    if removed:
        print(f"Redact rule removed: {args.table}.{args.column}")
        return 0
    print(f"No redact rule found for {args.table}.{args.column}")
    return 1


def cmd_redact_list(args: argparse.Namespace) -> int:
    config_dir = Path(args.config_dir) if hasattr(args, "config_dir") and args.config_dir else Path(".")
    rules = redact_module.load_redact_rules(config_dir)
    if not rules:
        print("No redact rules defined.")
        return 0
    for table, cols in sorted(rules.items()):
        for col in cols:
            print(f"  {table}.{col}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("redact", help="Manage column redaction rules")
    sub = p.add_subparsers(dest="redact_cmd", required=True)

    add_p = sub.add_parser("add", help="Add a redaction rule")
    add_p.add_argument("table", help="Table name")
    add_p.add_argument("column", help="Column name")
    add_p.add_argument("--config-dir", default=".", dest="config_dir")
    add_p.set_defaults(func=cmd_redact_add)

    rm_p = sub.add_parser("remove", help="Remove a redaction rule")
    rm_p.add_argument("table", help="Table name")
    rm_p.add_argument("column", help="Column name")
    rm_p.add_argument("--config-dir", default=".", dest="config_dir")
    rm_p.set_defaults(func=cmd_redact_remove)

    ls_p = sub.add_parser("list", help="List all redaction rules")
    ls_p.add_argument("--config-dir", default=".", dest="config_dir")
    ls_p.set_defaults(func=cmd_redact_list)
