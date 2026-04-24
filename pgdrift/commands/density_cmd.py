"""CLI command for schema density analysis."""
from __future__ import annotations

import argparse
import json
import sys

from pgdrift.config import load
from pgdrift.density import compute_density
from pgdrift.inspector import fetch_schema

import psycopg2


def cmd_density(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    try:
        profile = cfg.get_profile(args.profile)
    except KeyError:
        print(f"Unknown profile: {args.profile}", file=sys.stderr)
        return 1

    try:
        conn = psycopg2.connect(profile.dsn())
        tables = fetch_schema(conn, schema=getattr(args, "schema", "public"))
        conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    report = compute_density(tables)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    if not report.entries:
        print("No tables found.")
        return 0

    avg = report.average_score()
    print(f"Schema density report for profile '{args.profile}'")
    print(f"  Average density score : {avg:.2%}")
    print(f"  Tables analysed       : {len(report.entries)}")
    print()

    top = args.top if hasattr(args, "top") and args.top else 10
    least = report.least_dense(top)
    print(f"  Least dense tables (top {top}):")
    for entry in least:
        print(
            f"    {entry.table:<40} score={entry.density_score:.2%}"
            f"  ({entry.non_nullable_columns}/{entry.total_columns} required)"
        )

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "density",
        help="Analyse schema density (non-nullable column ratio) for a profile.",
    )
    p.add_argument("profile", help="Database profile name from pgdrift.yml")
    p.add_argument(
        "--schema", default="public", help="PostgreSQL schema to inspect (default: public)"
    )
    p.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of least-dense tables to display (default: 10)",
    )
    p.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    p.set_defaults(func=cmd_density)
