from __future__ import annotations
import argparse
import json
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.complexity import compute_complexity
import psycopg2


def cmd_complexity(args: argparse.Namespace) -> int:
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
        tables = fetch_schema(conn)
        conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}")
        return 1

    report = compute_complexity(tables)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    if not report.entries:
        print("No tables found.")
        return 0

    print(f"{'Table':<40} {'Cols':>5} {'Nullable':>8} {'Types':>6} {'Score':>7}")
    print("-" * 70)
    for e in sorted(report.entries, key=lambda x: x.score, reverse=True):
        print(f"{e.full_name:<40} {e.column_count:>5} {e.nullable_count:>8} {e.type_variety:>6} {e.score:>7.3f}")
    print()
    print(f"Average score: {report.average_score():.3f}")
    top = report.most_complex()
    if top:
        print(f"Most complex:  {top.full_name} (score={top.score})")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("complexity", help="Compute schema complexity for a profile")
    p.add_argument("profile", help="Profile name")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_complexity)
