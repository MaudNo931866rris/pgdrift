"""CLI commands for managing drift-check schedules."""

from __future__ import annotations

import argparse
import json
import sys

from pgdrift import schedule as sched


def cmd_schedule_add(args: argparse.Namespace) -> int:
    """Register a new named schedule."""
    if args.interval <= 0:
        print("error: interval must be a positive integer", file=sys.stderr)
        return 1
    entry = sched.add_schedule(
        name=args.name,
        source=args.source,
        target=args.target,
        interval_minutes=args.interval,
        directory=args.dir,
    )
    print(f"Schedule '{entry['name']}' saved ({entry['interval_minutes']} min).")
    return 0


def cmd_schedule_remove(args: argparse.Namespace) -> int:
    """Remove an existing schedule by name."""
    removed = sched.remove_schedule(args.name, directory=args.dir)
    if not removed:
        print(f"error: schedule '{args.name}' not found", file=sys.stderr)
        return 1
    print(f"Schedule '{args.name}' removed.")
    return 0


def cmd_schedule_list(args: argparse.Namespace) -> int:
    """List all registered schedules."""
    entries = sched.list_schedules(directory=args.dir)
    if not entries:
        print("No schedules configured.")
        return 0
    for e in entries:
        print(f"  {e['name']}: {e['source']} -> {e['target']} every {e['interval_minutes']} min")
    return 0


def cmd_schedule_show(args: argparse.Namespace) -> int:
    """Show details of a single schedule as JSON."""
    entry = sched.get_schedule(args.name, directory=args.dir)
    if entry is None:
        print(f"error: schedule '{args.name}' not found", file=sys.stderr)
        return 1
    print(json.dumps(entry, indent=2))
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("schedule", help="Manage drift-check schedules")
    p.add_argument("--dir", default=".", help="Directory for schedule storage")
    sub = p.add_subparsers(dest="schedule_cmd", required=True)

    add_p = sub.add_parser("add", help="Add a schedule")
    add_p.add_argument("name")
    add_p.add_argument("--source", required=True)
    add_p.add_argument("--target", required=True)
    add_p.add_argument("--interval", type=int, required=True, metavar="MINUTES")
    add_p.set_defaults(func=cmd_schedule_add)

    rm_p = sub.add_parser("remove", help="Remove a schedule")
    rm_p.add_argument("name")
    rm_p.set_defaults(func=cmd_schedule_remove)

    ls_p = sub.add_parser("list", help="List schedules")
    ls_p.set_defaults(func=cmd_schedule_list)

    show_p = sub.add_parser("show", help="Show a schedule")
    show_p.add_argument("name")
    show_p.set_defaults(func=cmd_schedule_show)
