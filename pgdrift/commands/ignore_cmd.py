"""CLI sub-commands for managing drift ignore rules."""

from __future__ import annotations

import argparse
import json

from pgdrift import ignore as ig


def cmd_ignore_add(args: argparse.Namespace) -> int:
    """Add an ignore pattern (table or column)."""
    if args.type == "table":
        ig.add_table_rule(args.pattern)
        print(f"Added table ignore pattern: {args.pattern}")
    else:
        ig.add_column_rule(args.pattern)
        print(f"Added column ignore pattern: {args.pattern}")
    return 0


def cmd_ignore_remove(args: argparse.Namespace) -> int:
    """Remove an existing ignore pattern."""
    removed = ig.remove_rule(args.pattern)
    if removed:
        print(f"Removed ignore pattern: {args.pattern}")
        return 0
    print(f"Pattern not found: {args.pattern}")
    return 1


def cmd_ignore_list(args: argparse.Namespace) -> int:
    """List all current ignore rules."""
    rules = ig.load_ignore()
    tables = rules.get("tables", [])
    columns = rules.get("columns", [])
    if not tables and not columns:
        print("No ignore rules defined.")
        return 0
    if tables:
        print("Tables:")
        for p in tables:
            print(f"  {p}")
    if columns:
        print("Columns:")
        for p in columns:
            print(f"  {p}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    ignore_parser = subparsers.add_parser("ignore", help="Manage drift ignore rules")
    sub = ignore_parser.add_subparsers(dest="ignore_cmd")

    add_p = sub.add_parser("add", help="Add an ignore pattern")
    add_p.add_argument("type", choices=["table", "column"], help="Rule type")
    add_p.add_argument("pattern", help="Glob pattern (e.g. public.audit_* or public.users.created_at)")
    add_p.set_defaults(func=cmd_ignore_add)

    rm_p = sub.add_parser("remove", help="Remove an ignore pattern")
    rm_p.add_argument("pattern", help="Exact pattern to remove")
    rm_p.set_defaults(func=cmd_ignore_remove)

    ls_p = sub.add_parser("list", help="List all ignore rules")
    ls_p.set_defaults(func=cmd_ignore_list)
