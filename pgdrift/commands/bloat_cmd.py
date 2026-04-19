"""CLI command for schema bloat detection."""
from __future__ import annotations
import argparse
import json
import sys
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.bloat import compute_bloat


def cmd_bloat(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    profile = get_profile(cfg, args.profile)
    if profile is None:
        print(f"Unknown profile: {args.profile}", file=sys.stderr)
        return 1

    import psycopg2
    try:
        conn = psycopg2.connect(profile.dsn())
        tables = fetch_schema(conn, schema=args.schema)
        conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    report = compute_bloat(
        tables,
        max_columns=args.max_columns,
        max_nullable_ratio=args.max_nullable_ratio,
    )

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 1 if report.any_bloat() else 0

    if not report.any_bloat():
        print("No schema bloat detected.")
        return 0

    print(f"Schema bloat detected in {len(report.entries)} table(s):")
    for entry in report.most_bloated(args.top):
        print(f"  {entry.table}: {entry.column_count} columns")
        for reason in entry.reasons:
            print(f"    - {reason}")
    return 1


def register(subparsers) -> None:
    p = subparsers.add_parser("bloat", help="Detect schema bloat")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--profile", required=True)
    p.add_argument("--schema", default="public")
    p.add_argument("--max-columns", type=int, default=30, dest="max_columns")
    p.add_argument(
        "--max-nullable-ratio", type=float, default=0.6, dest="max_nullable_ratio"
    )
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_bloat)
