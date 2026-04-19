"""CLI commands for column lineage tracking."""

from __future__ import annotations

import argparse
import json

from pgdrift import lineage as lin


def cmd_lineage_list(args: argparse.Namespace) -> int:
    labels = lin.list_lineage()
    if not labels:
        print("No lineage records found.")
        return 0
    for label in labels:
        print(label)
    return 0


def cmd_lineage_show(args: argparse.Namespace) -> int:
    report = lin.load_lineage(args.label)
    if report is None:
        print(f"No lineage record found for '{args.label}'.")
        return 1

    if args.table:
        events = report.for_table(args.table)
    else:
        events = report.events

    if not events:
        print("No events found.")
        return 0

    print(json.dumps([e.__dict__ for e in events], indent=2))
    return 0


def cmd_lineage_clear(args: argparse.Namespace) -> int:
    import shutil
    from pathlib import Path
    p = Path(".pgdrift") / "lineage"
    if p.exists():
        shutil.rmtree(p)
        print("Lineage records cleared.")
    else:
        print("Nothing to clear.")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("lineage", help="Column lineage commands")
    sub = p.add_subparsers(dest="lineage_cmd")

    sub.add_parser("list", help="List lineage records").set_defaults(func=cmd_lineage_list)

    show_p = sub.add_parser("show", help="Show lineage events")
    show_p.add_argument("label", help="Lineage record label")
    show_p.add_argument("--table", default=None, help="Filter by table name")
    show_p.set_defaults(func=cmd_lineage_show)

    sub.add_parser("clear", help="Clear all lineage records").set_defaults(func=cmd_lineage_clear)
