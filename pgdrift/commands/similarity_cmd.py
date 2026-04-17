"""CLI command: pgdrift similarity — show schema similarity score."""
from __future__ import annotations
import argparse
import json
import sys
import psycopg2
from pgdrift.config import load
from pgdrift.inspector import fetch_schema
from pgdrift.similarity import compute_similarity


def cmd_similarity(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    try:
        src_profile = cfg.get_profile(args.source)
        tgt_profile = cfg.get_profile(args.target)
    except KeyError as exc:
        print(f"Unknown profile: {exc}", file=sys.stderr)
        return 1

    try:
        with psycopg2.connect(src_profile.dsn()) as src_conn:
            source_tables = fetch_schema(src_conn)
        with psycopg2.connect(tgt_profile.dsn()) as tgt_conn:
            target_tables = fetch_schema(tgt_conn)
    except Exception as exc:  # noqa: BLE001
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    result = compute_similarity(source_tables, target_tables)

    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(f"Similarity score : {result.score:.2%}")
        print(f"Matched tables   : {result.matched}/{result.total}")
        if args.verbose:
            for name, score in sorted(result.per_table.items()):
                print(f"  {name}: {score:.2%}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("similarity", help="Show schema similarity score between two environments")
    p.add_argument("source", help="Source profile name")
    p.add_argument("target", help="Target profile name")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--verbose", "-v", action="store_true", help="Show per-table scores")
    p.set_defaults(func=cmd_similarity)
