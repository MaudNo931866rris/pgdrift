"""CLI command: pgdrift scorecard – print a drift health score."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from pgdrift.config import load
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.scorecard import compute_scorecard


def cmd_scorecard(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    try:
        src_profile = cfg.get_profile(args.source)
    except KeyError:
        print(f"Unknown profile: {args.source}", file=sys.stderr)
        return 1

    try:
        tgt_profile = cfg.get_profile(args.target)
    except KeyError:
        print(f"Unknown profile: {args.target}", file=sys.stderr)
        return 1

    import psycopg2  # type: ignore

    with psycopg2.connect(src_profile.dsn) as src_conn:
        source_tables = fetch_schema(src_conn, schemas=args.schemas)

    with psycopg2.connect(tgt_profile.dsn) as tgt_conn:
        target_tables = fetch_schema(tgt_conn, schemas=args.schemas)

    report = compute_drift(args.source, args.target, source_tables, target_tables)
    card = compute_scorecard(report, total_tables=len(source_tables) or 1)

    if args.json:
        print(json.dumps(card.as_dict(), indent=2))
    else:
        print(f"Drift Scorecard  [{card.source}  →  {card.target}]")
        print(f"  Tables (source) : {card.total_tables}")
        print(f"  Added           : {card.added_tables}")
        print(f"  Removed         : {card.removed_tables}")
        print(f"  Modified        : {card.modified_tables}")
        print(f"  Column changes  : {card.total_column_changes}")
        print(f"  Score           : {card.score:.1f} / 100  [{card.grade}]")

    return 0 if card.score >= (args.min_score or 0) else 1


def register(subparsers) -> None:
    p = subparsers.add_parser("scorecard", help="Print a numeric drift health score")
    p.add_argument("source", help="Source profile name")
    p.add_argument("target", help="Target profile name")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--schemas", nargs="*", default=None)
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument(
        "--min-score",
        dest="min_score",
        type=float,
        default=None,
        help="Exit with code 1 if score is below this value",
    )
    p.set_defaults(func=cmd_scorecard)
