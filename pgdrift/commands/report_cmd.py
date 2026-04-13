"""CLI command: pgdrift report — export drift as Markdown or HTML."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pgdrift import config as cfg
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.reporter import render, ReportFormat


def cmd_report(args: argparse.Namespace) -> int:
    try:
        conf = cfg.load(args.config)
    except FileNotFoundError:
        print(f"[error] config file not found: {args.config}", file=sys.stderr)
        return 1

    try:
        source_profile = cfg.get_profile(conf, args.source)
        target_profile = cfg.get_profile(conf, args.target)
    except KeyError as exc:
        print(f"[error] unknown profile: {exc}", file=sys.stderr)
        return 1

    fmt: ReportFormat = args.format

    import psycopg2  # type: ignore

    try:
        with psycopg2.connect(cfg.dsn(source_profile)) as src_conn:
            source_tables = fetch_schema(src_conn, args.schema)
        with psycopg2.connect(cfg.dsn(target_profile)) as tgt_conn:
            target_tables = fetch_schema(tgt_conn, args.schema)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] database connection failed: {exc}", file=sys.stderr)
        return 1

    report = compute_drift(source_tables, target_tables)
    output = render(fmt, args.source, args.target, report)

    out_path = Path(args.output)
    out_path.write_text(output, encoding="utf-8")
    print(f"Report written to {out_path}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("report", help="Export drift report as Markdown or HTML")
    p.add_argument("source", help="Source profile name")
    p.add_argument("target", help="Target profile name")
    p.add_argument(
        "--format",
        choices=["markdown", "html"],
        default="markdown",
        dest="format",
        help="Output format (default: markdown)",
    )
    p.add_argument(
        "--output",
        default="drift_report.md",
        help="Output file path (default: drift_report.md)",
    )
    p.add_argument(
        "--schema",
        default="public",
        help="PostgreSQL schema to inspect (default: public)",
    )
    p.add_argument(
        "--config",
        default="pgdrift.yml",
        help="Path to config file (default: pgdrift.yml)",
    )
    p.set_defaults(func=cmd_report)
