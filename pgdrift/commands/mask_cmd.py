"""CLI sub-commands for managing column masking rules."""

from __future__ import annotations

import argparse

from pgdrift import mask as mask_module


def cmd_mask_add(args: argparse.Namespace) -> int:
    mask_module.add_mask(args.column, args.alias, directory=args.dir)
    print(f"Masked column '{args.column}' -> '{args.alias}'")
    return 0


def cmd_mask_remove(args: argparse.Namespace) -> int:
    removed = mask_module.remove_mask(args.column, directory=args.dir)
    if not removed:
        print(f"No mask found for column '{args.column}'")
        return 1
    print(f"Removed mask for column '{args.column}'")
    return 0


def cmd_mask_list(args: argparse.Namespace) -> int:
    entries = mask_module.list_masks(directory=args.dir)
    if not entries:
        print("No masks defined.")
        return 0
    for entry in entries:
        print(f"  {entry['column']} -> {entry['alias']}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    mask_p = subparsers.add_parser("mask", help="Manage column masking rules")
    mask_sub = mask_p.add_subparsers(dest="mask_cmd")

    add_p = mask_sub.add_parser("add", help="Add or update a mask")
    add_p.add_argument("column", help="Real column name")
    add_p.add_argument("alias", help="Alias to display instead")
    add_p.add_argument("--dir", default=".", help="Directory for mask file")
    add_p.set_defaults(func=cmd_mask_add)

    rm_p = mask_sub.add_parser("remove", help="Remove a mask")
    rm_p.add_argument("column", help="Column name to un-mask")
    rm_p.add_argument("--dir", default=".", help="Directory for mask file")
    rm_p.set_defaults(func=cmd_mask_remove)

    ls_p = mask_sub.add_parser("list", help="List all masks")
    ls_p.add_argument("--dir", default=".", help="Directory for mask file")
    ls_p.set_defaults(func=cmd_mask_list)
