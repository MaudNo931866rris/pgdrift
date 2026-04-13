"""CLI commands for managing pgdrift tags."""

from __future__ import annotations

import argparse
from typing import List

from pgdrift import tags as tag_store


def cmd_tag_add(args: argparse.Namespace) -> int:
    """Tag a snapshot or baseline file with a friendly name."""
    tag_store.add_tag(args.tag, args.filename, directory=args.directory)
    print(f"Tagged '{args.filename}' as '{args.tag}'.")
    return 0


def cmd_tag_remove(args: argparse.Namespace) -> int:
    """Remove a tag."""
    removed = tag_store.remove_tag(args.tag, directory=args.directory)
    if not removed:
        print(f"Tag '{args.tag}' not found.")
        return 1
    print(f"Removed tag '{args.tag}'.")
    return 0


def cmd_tag_list(args: argparse.Namespace) -> int:
    """List all tags."""
    entries = tag_store.list_tags(directory=args.directory)
    if not entries:
        print("No tags defined.")
        return 0
    for entry in entries:
        print(f"{entry['tag']:30s}  {entry['filename']}")
    return 0


def cmd_tag_resolve(args: argparse.Namespace) -> int:
    """Print the filename associated with a tag."""
    filename = tag_store.resolve_tag(args.tag, directory=args.directory)
    if filename is None:
        print(f"Tag '{args.tag}' not found.")
        return 1
    print(filename)
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    tag_parser = subparsers.add_parser("tag", help="Manage snapshot/baseline tags")
    tag_sub = tag_parser.add_subparsers(dest="tag_command")

    add_p = tag_sub.add_parser("add", help="Add a tag")
    add_p.add_argument("tag", help="Tag name")
    add_p.add_argument("filename", help="Snapshot or baseline filename")
    add_p.add_argument("--directory", default=".", help="Working directory")
    add_p.set_defaults(func=cmd_tag_add)

    rm_p = tag_sub.add_parser("remove", help="Remove a tag")
    rm_p.add_argument("tag", help="Tag name")
    rm_p.add_argument("--directory", default=".", help="Working directory")
    rm_p.set_defaults(func=cmd_tag_remove)

    ls_p = tag_sub.add_parser("list", help="List all tags")
    ls_p.add_argument("--directory", default=".", help="Working directory")
    ls_p.set_defaults(func=cmd_tag_list)

    res_p = tag_sub.add_parser("resolve", help="Resolve a tag to a filename")
    res_p.add_argument("tag", help="Tag name")
    res_p.add_argument("--directory", default=".", help="Working directory")
    res_p.set_defaults(func=cmd_tag_resolve)
