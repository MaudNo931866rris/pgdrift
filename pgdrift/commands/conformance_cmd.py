"""CLI command: pgdrift conformance — check schema naming/type conventions."""
from __future__ import annotations

import argparse
import json
import sys

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.conformance import compute_conformance

import psycopg2


def cmd_conformance(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    profile = get_profile(cfg, args.profile)
    if profile is None:
        print(f"Unknown profile: {args.profile}", file=sys.stderr)
        return 1

    try:
        conn = psycopg2.connect(profile.dsn)
    except Exception as exc:  # pragma: no cover
        print(f"Connection failed: {exc}", file=sys.stderr)
        return 1

    try:
        tables = fetch_schema(conn, schema=args.schema)
    finally:
        conn.close()

    report = compute_conformance(tables)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 1 if report.any_violations else 0

    if not report.any_violations:
        print("No conformance violations found.")
        return 0

    print(f"Found {report.violation_count} conformance violation(s):")
    for v in report.violations:
        loc = f"{v.table}.{v.column}" if v.column else v.table
        print(f"  [{v.rule}] {loc}: {v.detail}")

    return 1


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "conformance",
        help="Check schema naming and type conventions",
    )
    p.add_argument("profile", help="Database profile name from pgdrift.yml")
    p.add_argument("--schema", default="public", help="PostgreSQL schema (default: public)")
    p.add_argument("--json", action="store_true", help="Output results as JSON")
    p.add_argument(
        "--config",
        default="pgdrift.yml",
        help="Path to config file (default: pgdrift.yml)",
    )
    p.set_defaults(func=cmd_conformance)
