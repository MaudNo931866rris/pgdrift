"""CLI command for shadow schema detection."""
from __future__ import annotations
import argparse
import json
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.shadow import compute_shadow
import psycopg2


def cmd_shadow(args: argparse.Namespace) -> int:
    cfg = load(args.config)
    if cfg is None:
        print("[error] config file not found")
        return 1

    profile = get_profile(cfg, args.profile)
    if profile is None:
        print(f"[error] unknown profile: {args.profile}")
        return 1

    try:
        conn = psycopg2.connect(profile.dsn)
        live_tables = fetch_schema(conn)
        conn.close()
    except Exception as exc:
        print(f"[error] connection failed: {exc}")
        return 1

    live_map = {t.full_name(): t for t in live_tables}
    report = compute_shadow(args.pin, live_map)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 1 if report.any_shadow() else 0

    if not report.any_shadow():
        print(f"No shadow drift detected against pin '{args.pin}'.")
        return 0

    print(f"Shadow drift detected against pin '{args.pin}':")
    for e in report.entries:
        print(f"  {e.table}")
        for c in e.drift.added_columns:
            print(f"    + {c.name} (added)")
        for c in e.drift.removed_columns:
            print(f"    - {c.name} (removed)")
        for c in e.drift.modified_columns:
            print(f"    ~ {c.name} (modified)")
    return 1


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("shadow", help="Detect schema drift against a pinned reference")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--profile", required=True)
    p.add_argument("--pin", required=True, help="Pin label to compare against")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_shadow)
