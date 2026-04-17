"""CLI command: pgdrift revert — show SQL stubs to undo detected drift."""
from __future__ import annotations
import argparse
import sys
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.revert import build_revert_plan
import psycopg2


def cmd_revert(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    src_profile = get_profile(cfg, args.source)
    if src_profile is None:
        print(f"Unknown source profile: {args.source}", file=sys.stderr)
        return 1

    tgt_profile = get_profile(cfg, args.target)
    if tgt_profile is None:
        print(f"Unknown target profile: {args.target}", file=sys.stderr)
        return 1

    try:
        with psycopg2.connect(src_profile.dsn) as src_conn:
            source_tables = fetch_schema(src_conn)
        with psycopg2.connect(tgt_profile.dsn) as tgt_conn:
            target_tables = fetch_schema(tgt_conn)
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    report = compute_drift(args.source, args.target, source_tables, target_tables)
    plan = build_revert_plan(report)

    if plan.is_empty():
        print("No drift detected — nothing to revert.")
        return 0

    print(f"-- Revert plan: {args.source} <- {args.target}")
    print(f"-- {len(plan.statements)} statement(s)\n")
    for stmt in plan.statements:
        print(f"-- {stmt.reason}")
        print(stmt.sql)
        print()
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("revert", help="Show SQL stubs to revert schema drift")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--source", required=True)
    p.add_argument("--target", required=True)
    p.set_defaults(func=cmd_revert)
