"""CLI command: pgdrift cohesion — show per-table cohesion scores."""
from __future__ import annotations

import argparse
import json
from typing import List

import psycopg2

from pgdrift.cohesion import compute_cohesion
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema


def cmd_cohesion(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        return 1

    profile = get_profile(cfg, args.profile)
    if profile is None:
        print(f"Unknown profile: {args.profile}")
        return 1

    try:
        conn = psycopg2.connect(profile.dsn)
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}")
        return 1

    try:
        tables = fetch_schema(conn, schema=getattr(args, "schema", "public"))
    finally:
        conn.close()

    report = compute_cohesion(tables)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    if not report.entries:
        print("No tables found.")
        return 0

    print(f"{'Table':<40} {'Cols':>5} {'Types':>6} {'Prefixes':>9} {'Score':>7}")
    print("-" * 72)
    for e in sorted(report.entries, key=lambda x: x.score):
        print(
            f"{e.table:<40} {e.column_count:>5} {e.type_variety:>6} "
            f"{e.prefix_groups:>9} {e.score:>7.3f}"
        )
    print("-" * 72)
    print(f"Average cohesion score: {report.average_score():.3f}")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("cohesion", help="Show per-table cohesion scores")
    p.add_argument("profile", help="Database profile name")
    p.add_argument("--schema", default="public", help="PostgreSQL schema (default: public)")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--config", default="pgdrift.yml")
    p.set_defaults(func=cmd_cohesion)
