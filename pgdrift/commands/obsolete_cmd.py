"""CLI command: pgdrift obsolete — list obsolete columns across environments."""
from __future__ import annotations
import argparse
import json

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.obsolete import compute_obsolete

import psycopg2


def cmd_obsolete(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        return 1

    source = get_profile(cfg, args.source)
    if source is None:
        print(f"Unknown profile: {args.source}")
        return 1

    target = get_profile(cfg, args.target)
    if target is None:
        print(f"Unknown profile: {args.target}")
        return 1

    with psycopg2.connect(source.dsn) as sc:
        source_tables = fetch_schema(sc)
    with psycopg2.connect(target.dsn) as tc:
        target_tables = fetch_schema(tc)

    drift = compute_drift(source_tables, target_tables)
    report = compute_obsolete(drift)

    if not report.any_obsolete():
        print("No obsolete columns detected.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(report.as_dict(), indent=2))
    else:
        for e in report.entries:
            print(f"  {e.schema}.{e.table}.{e.column}  ({e.data_type})")

    return 1


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("obsolete", help="List obsolete columns removed in target")
    p.add_argument("--source", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_obsolete)
