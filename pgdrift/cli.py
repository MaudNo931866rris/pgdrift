"""CLI entry point for pgdrift."""

import sys
import argparse

import psycopg2

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.diff import build_report
from pgdrift.formatter import format_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pgdrift",
        description="Detect and summarize schema drift between PostgreSQL environments.",
    )
    parser.add_argument(
        "--config",
        default="pgdrift.yml",
        help="Path to config file (default: pgdrift.yml)",
    )
    parser.add_argument(
        "source",
        help="Source environment profile name",
    )
    parser.add_argument(
        "target",
        help="Target environment profile name",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    parser.add_argument(
        "--schema",
        default="public",
        help="PostgreSQL schema to inspect (default: public)",
    )
    return parser


def run(args=None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    try:
        config = load(parsed.config)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        source_profile = get_profile(config, parsed.source)
        target_profile = get_profile(config, parsed.target)
    except KeyError as exc:
        print(f"Error: profile {exc} not found in config.", file=sys.stderr)
        return 1

    try:
        with psycopg2.connect(source_profile.dsn()) as src_conn:
            source_schema = fetch_schema(src_conn, schema=parsed.schema)
        with psycopg2.connect(target_profile.dsn()) as tgt_conn:
            target_schema = fetch_schema(tgt_conn, schema=parsed.schema)
    except Exception as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    report = build_report(source_schema, target_schema, parsed.source, parsed.target)
    output = format_report(report, use_color=not parsed.no_color)
    print(output)

    return 1 if report.has_drift() else 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
