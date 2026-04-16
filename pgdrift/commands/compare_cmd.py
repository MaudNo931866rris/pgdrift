"""CLI command: pgdrift compare — diff live schema vs baseline or snapshot."""
from __future__ import annotations

import argparse
import sys

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.compare import compare_against_baseline, compare_against_snapshot
from pgdrift.formatter import format_report

import psycopg2


def cmd_compare(args: argparse.Namespace) -> int:
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
        live_tables = fetch_schema(conn, schema=args.schema)
        conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    if args.baseline:
        result = compare_against_baseline(
            live_tables, args.profile, args.baseline, baselines_dir=args.baselines_dir
        )
        if result is None:
            print(f"Baseline '{args.baseline}' not found for profile '{args.profile}'.", file=sys.stderr)
            return 1
    elif args.snapshot:
        result = compare_against_snapshot(live_tables, args.profile, args.snapshot)
        if result is None:
            print(f"Snapshot file not found: {args.snapshot}", file=sys.stderr)
            return 1
    else:
        print("Provide --baseline LABEL or --snapshot FILE.", file=sys.stderr)
        return 1

    print(format_report(result.report, use_color=not args.no_color))
    return 1 if result.report.has_drift else 0


def register(subparsers) -> None:
    p = subparsers.add_parser("compare", help="Compare live schema to a baseline or snapshot")
    p.add_argument("profile", help="Database profile name")
    p.add_argument("--baseline", metavar="LABEL", help="Baseline label to compare against")
    p.add_argument("--snapshot", metavar="FILE", help="Snapshot file to compare against")
    p.add_argument("--schema", default="public")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--baselines-dir", default=None)
    p.add_argument("--no-color", action="store_true")
    p.set_defaults(func=cmd_compare)
