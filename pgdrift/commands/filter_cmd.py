"""CLI commands for managing schema/table filter rules."""

from __future__ import annotations

import argparse

from pgdrift import filter as fil


def cmd_filter_add(args: argparse.Namespace) -> int:
    if args.kind == "schema":
        fil.add_schema_filter(args.value)
        print(f"Added schema filter: {args.value}")
    else:
        fil.add_table_filter(args.value)
        print(f"Added table filter pattern: {args.value}")
    return 0


def cmd_filter_remove(args: argparse.Namespace) -> int:
    removed = fil.remove_filter(args.value, args.kind)
    if removed:
        print(f"Removed {args.kind} filter: {args.value}")
        return 0
    print(f"Filter not found: {args.value}")
    return 1


def cmd_filter_list(args: argparse.Namespace) -> int:
    filters = fil.load_filters()
    schemas = filters.get("schemas", [])
    tables = filters.get("tables", [])
    if not schemas and not tables:
        print("No filters defined.")
        return 0
    if schemas:
        print("Schema filters:")
        for s in schemas:
            print(f"  {s}")
    if tables:
        print("Table pattern filters:")
        for t in tables:
            print(f"  {t}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("filter", help="Manage schema/table filters")
    sub = p.add_subparsers(dest="filter_cmd")

    add_p = sub.add_parser("add", help="Add a filter rule")
    add_p.add_argument("kind", choices=["schema", "table"], help="Filter type")
    add_p.add_argument("value", help="Schema name or table glob pattern")
    add_p.set_defaults(func=cmd_filter_add)

    rm_p = sub.add_parser("remove", help="Remove a filter rule")
    rm_p.add_argument("kind", choices=["schema", "table"], help="Filter type")
    rm_p.add_argument("value", help="Value to remove")
    rm_p.set_defaults(func=cmd_filter_remove)

    ls_p = sub.add_parser("list", help="List all filter rules")
    ls_p.set_defaults(func=cmd_filter_list)
