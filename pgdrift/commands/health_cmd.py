"""CLI command: pgdrift health — show schema health for a profile."""
from __future__ import annotations

import argparse
import json
import sys

import psycopg2

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.health import compute_health


def cmd_health(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    profile = get_profile(cfg, args.profile)
    if profile is None:
        print(f"Unknown profile: {args.profile}", file=sys.stderr)
        return 1

    baseline_profile = get_profile(cfg, args.baseline) if args.baseline else None
    if args.baseline and baseline_profile is None:
        print(f"Unknown baseline profile: {args.baseline}", file=sys.stderr)
        return 1

    try:
        conn = psycopg2.connect(profile.dsn)
        tables = fetch_schema(conn)
        conn.close()

        if baseline_profile:
            bconn = psycopg2.connect(baseline_profile.dsn)
            baseline_tables = fetch_schema(bconn)
            bconn.close()
            report = compute_drift(baseline_tables, tables)
        else:
            from pgdrift.diff import DriftReport
            report = DriftReport(source=args.profile, target=args.profile, table_diffs=[])

    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    health = compute_health(args.profile, report, tables)

    if args.json:
        print(json.dumps(health.as_dict(), indent=2))
    else:
        d = health.as_dict()
        print(f"Profile : {d['profile']}")
        print(f"Grade   : {d['grade']}  (score {d['score']:.1f})")
        print(f"Lint    : {d['lint_errors']} error(s), {d['lint_warnings']} warning(s)")
        print(f"Changes : {d['total_changes']}  destructive={d['has_destructive']}")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("health", help="Show schema health for a profile")
    p.add_argument("profile", help="Profile name")
    p.add_argument("--baseline", default=None, help="Baseline profile for drift comparison")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_health)
