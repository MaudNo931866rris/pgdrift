"""CLI command: pgdrift impact — show drift impact assessment."""
from __future__ import annotations
import argparse
import json
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.impact import compute_impact
import psycopg2


def cmd_impact(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        return 1

    source = get_profile(cfg, args.source)
    if source is None:
        print(f"Unknown profile: {args.source}")
        return 1

    target = get_profile(cfg, args.target)
    if target is None:
        print(f"Unknown profile: {args.target}")
        return 1

    try:
        src_conn = psycopg2.connect(source.dsn)
        tgt_conn = psycopg2.connect(target.dsn)
        src_tables = fetch_schema(src_conn)
        tgt_tables = fetch_schema(tgt_conn)
        src_conn.close()
        tgt_conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}")
        return 1

    report = compute_drift(args.source, args.target, src_tables, tgt_tables)
    impact = compute_impact(report)
    data = impact.as_dict()

    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        if not impact.items:
            print("No drift detected — no impact.")
            return 0
        print(f"Impact Assessment: {args.source} → {args.target}")
        print(f"  Critical: {data['critical_count']}  High: {data['high_count']}")
        for item in impact.items:
            print(f"  [{item.severity.upper():8s}] {item.table} ({item.change_type}): {item.reason}")
    return 1 if impact.critical() else 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("impact", help="Assess impact severity of schema drift")
    p.add_argument("source", help="Source profile name")
    p.add_argument("target", help="Target profile name")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_impact)
