"""CLI commands for pinning schema states."""
from __future__ import annotations

import argparse
import sys

from pgdrift.config import load
from pgdrift.inspector import fetch_schema
from pgdrift.pin import save_pin, load_pin, delete_pin, list_pins

import psycopg2


def cmd_pin_save(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1
    profile = cfg.get_profile(args.profile)
    if profile is None:
        print(f"Unknown profile: {args.profile}", file=sys.stderr)
        return 1
    conn = psycopg2.connect(profile.dsn)
    try:
        tables = fetch_schema(conn)
    finally:
        conn.close()
    path = save_pin(args.profile, tables)
    print(f"Pinned schema for '{args.profile}' → {path}")
    return 0


def cmd_pin_show(args: argparse.Namespace) -> int:
    data = load_pin(args.profile)
    if data is None:
        print(f"No pin found for profile '{args.profile}'", file=sys.stderr)
        return 1
    print(f"Profile : {data['profile']}")
    print(f"Pinned  : {data['pinned_at']}")
    print(f"Tables  : {len(data['tables'])}")
    for t in data["tables"]:
        print(f"  {t['schema']}.{t['name']} ({len(t['columns'])} columns)")
    return 0


def cmd_pin_delete(args: argparse.Namespace) -> int:
    removed = delete_pin(args.profile)
    if not removed:
        print(f"No pin found for profile '{args.profile}'", file=sys.stderr)
        return 1
    print(f"Deleted pin for '{args.profile}'")
    return 0


def cmd_pin_list(args: argparse.Namespace) -> int:
    pins = list_pins()
    if not pins:
        print("No pins saved.")
    for p in pins:
        print(p)
    return 0


def register(subparsers) -> None:
    pin_p = subparsers.add_parser("pin", help="Pin schema states")
    pin_sub = pin_p.add_subparsers(dest="pin_cmd")

    save_p = pin_sub.add_parser("save", help="Pin current schema for a profile")
    save_p.add_argument("profile")
    save_p.add_argument("--config", default="pgdrift.yml")
    save_p.set_defaults(func=cmd_pin_save)

    show_p = pin_sub.add_parser("show", help="Show pinned schema")
    show_p.add_argument("profile")
    show_p.set_defaults(func=cmd_pin_show)

    del_p = pin_sub.add_parser("delete", help="Delete a pin")
    del_p.add_argument("profile")
    del_p.set_defaults(func=cmd_pin_delete)

    lst_p = pin_sub.add_parser("list", help="List all pins")
    lst_p.set_defaults(func=cmd_pin_list)
