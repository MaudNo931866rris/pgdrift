"""CLI command: pgdrift maturity"""
from __future__ import annotations
import argparse
import json

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.lint import lint_tables
from pgdrift.drift_age import DriftAgeReport
from pgdrift.summary import summarise
from pgdrift.maturity import compute_maturity

import psycopg2


def cmd_maturity(args: argparse.Namespace) -> int:
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
        tables = fetch_schema(conn, schema=args.schema)
        conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}")
        return 1

    lint_result = lint_tables(tables)
    age_report = DriftAgeReport(entries=[])  # empty unless audit dir provided

    result = compute_maturity(
        profile=args.profile,
        lint_result=lint_result,
        age_report=age_report,
    )

    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(f"Profile : {result.profile}")
        print(f"Score   : {result.score:.1f} / 100  [{result.grade}]")
        if result.penalties:
            print("Penalties:")
            for p in result.penalties:
                print(f"  {p}")
        else:
            print("No penalties.")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("maturity", help="Compute schema maturity score")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--profile", required=True)
    p.add_argument("--schema", default="public")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_maturity)
