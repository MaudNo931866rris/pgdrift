"""CLI sub-commands for baseline management."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pgdrift import baseline as bl
from pgdrift.config import load as load_config, ConfigError


def cmd_baseline_save(args: argparse.Namespace) -> int:
    """Capture a named baseline from a list of table names (stdin or --tables)."""
    tables: list[str] = []
    if args.tables:
        tables = [t.strip() for t in args.tables.split(",") if t.strip()]
    else:
        tables = [line.strip() for line in sys.stdin if line.strip()]

    if not tables:
        print("error: no table names provided", file=sys.stderr)
        return 1

    path = bl.save_baseline(
        name=args.name,
        table_names=tables,
        note=args.note,
        base_dir=Path(args.baseline_dir),
    )
    print(f"Baseline '{args.name}' saved to {path}")
    return 0


def cmd_baseline_list(args: argparse.Namespace) -> int:
    """List all saved baselines."""
    names = bl.list_baselines(base_dir=Path(args.baseline_dir))
    if not names:
        print("No baselines found.")
    else:
        for name in names:
            print(name)
    return 0


def cmd_baseline_show(args: argparse.Namespace) -> int:
    """Print details of a named baseline."""
    entry = bl.load_baseline(args.name, base_dir=Path(args.baseline_dir))
    if entry is None:
        print(f"error: baseline '{args.name}' not found", file=sys.stderr)
        return 1
    print(json.dumps(entry, indent=2))
    return 0


def cmd_baseline_delete(args: argparse.Namespace) -> int:
    """Delete a named baseline."""
    deleted = bl.delete_baseline(args.name, base_dir=Path(args.baseline_dir))
    if not deleted:
        print(f"error: baseline '{args.name}' not found", file=sys.stderr)
        return 1
    print(f"Baseline '{args.name}' deleted.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("baseline", help="Manage drift baselines")
    p.add_argument("--baseline-dir", default=".pgdrift/baselines")
    sub = p.add_subparsers(dest="baseline_action", required=True)

    save_p = sub.add_parser("save", help="Save a new baseline")
    save_p.add_argument("name", help="Baseline name")
    save_p.add_argument("--tables", default="", help="Comma-separated table names")
    save_p.add_argument("--note", default="", help="Optional note")
    save_p.set_defaults(func=cmd_baseline_save)

    list_p = sub.add_parser("list", help="List baselines")
    list_p.set_defaults(func=cmd_baseline_list)

    show_p = sub.add_parser("show", help="Show a baseline")
    show_p.add_argument("name")
    show_p.set_defaults(func=cmd_baseline_show)

    del_p = sub.add_parser("delete", help="Delete a baseline")
    del_p.add_argument("name")
    del_p.set_defaults(func=cmd_baseline_delete)
