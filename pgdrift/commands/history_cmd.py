"""CLI command for managing and displaying snapshot history."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import List

HISTORY_DIR = ".pgdrift_history"


def _list_snapshots(directory: str) -> List[str]:
    """Return sorted list of snapshot files in the history directory."""
    if not os.path.isdir(directory):
        return []
    files = [
        f for f in os.listdir(directory) if f.endswith(".json")
    ]
    return sorted(files)


def cmd_history_list(args: argparse.Namespace) -> int:
    """List all saved snapshots in the history directory."""
    directory = getattr(args, "history_dir", HISTORY_DIR)
    snapshots = _list_snapshots(directory)
    if not snapshots:
        print("No snapshots found.")
        return 0
    print(f"Snapshots in '{directory}':")
    for name in snapshots:
        path = os.path.join(directory, name)
        mtime = os.path.getmtime(path)
        ts = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {name}  ({ts})")
    return 0


def cmd_history_show(args: argparse.Namespace) -> int:
    """Print the contents of a named snapshot file."""
    directory = getattr(args, "history_dir", HISTORY_DIR)
    name = args.name
    if not name.endswith(".json"):
        name = name + ".json"
    path = os.path.join(directory, name)
    if not os.path.exists(path):
        print(f"Snapshot not found: {path}")
        return 1
    with open(path) as fh:
        data = json.load(fh)
    print(json.dumps(data, indent=2))
    return 0


def cmd_history_clear(args: argparse.Namespace) -> int:
    """Remove all snapshots from the history directory."""
    directory = getattr(args, "history_dir", HISTORY_DIR)
    snapshots = _list_snapshots(directory)
    if not snapshots:
        print("Nothing to clear.")
        return 0
    for name in snapshots:
        os.remove(os.path.join(directory, name))
    print(f"Removed {len(snapshots)} snapshot(s).")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("history", help="Manage snapshot history")
    parser.add_argument("--history-dir", default=HISTORY_DIR, dest="history_dir")
    sub = parser.add_subparsers(dest="history_action")

    sub.add_parser("list", help="List saved snapshots")

    show_p = sub.add_parser("show", help="Show contents of a snapshot")
    show_p.add_argument("name", help="Snapshot filename (without .json)")

    sub.add_parser("clear", help="Delete all snapshots")

    def _dispatch(args: argparse.Namespace) -> int:
        action = getattr(args, "history_action", None)
        if action == "list" or action is None:
            return cmd_history_list(args)
        if action == "show":
            return cmd_history_show(args)
        if action == "clear":
            return cmd_history_clear(args)
        print(f"Unknown history action: {action}")
        return 1

    parser.set_defaults(func=_dispatch)
