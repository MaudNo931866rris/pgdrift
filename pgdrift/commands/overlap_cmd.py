"""CLI command for schema column overlap analysis."""
from __future__ import annotations
import json
import argparse
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.overlap import compute_overlap
import psycopg2


def cmd_overlap(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        return 1

    source_profile = get_profile(cfg, args.source)
    if source_profile is None:
        print(f"Unknown profile: {args.source}")
        return 1

    target_profile = get_profile(cfg, args.target)
    if target_profile is None:
        print(f"Unknown profile: {args.target}")
        return 1

    try:
        src_conn = psycopg2.connect(source_profile.dsn)
        tgt_conn = psycopg2.connect(target_profile.dsn)
        source_schema = fetch_schema(src_conn)
        target_schema = fetch_schema(tgt_conn)
        src_conn.close()
        tgt_conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}")
        return 1

    report = compute_overlap(source_schema, target_schema)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    if not report.entries:
        print("No common tables found between profiles.")
        return 0

    for entry in report.entries:
        ratio = entry.overlap_ratio()
        print(f"\n[{entry.table}]  overlap={ratio:.0%}")
        if entry.shared_columns:
            print(f"  shared  : {', '.join(entry.shared_columns)}")
        if entry.source_only:
            print(f"  src only: {', '.join(entry.source_only)}")
        if entry.target_only:
            print(f"  tgt only: {', '.join(entry.target_only)}")

    return 1 if report.any_divergence() else 0


def register(subparsers) -> None:
    p = subparsers.add_parser("overlap", help="Show column overlap between two profiles")
    p.add_argument("source", help="Source profile name")
    p.add_argument("target", help="Target profile name")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_overlap)
