"""CLI command for comparing two live database profiles and reporting drift."""

from __future__ import annotations

import sys
from argparse import Namespace
from typing import Optional

import psycopg2

from pgdrift.config import Config, load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.formatter import format_report


def cmd_diff(args: Namespace, config_path: str = "pgdrift.yml") -> int:
    """Compare two profiles from live databases and print a drift report.

    Args:
        args: Parsed CLI arguments. Expected attributes:
            - source (str): name of the source profile
            - target (str): name of the target profile
            - no_color (bool): disable colorized output
        config_path: Path to the pgdrift YAML configuration file.

    Returns:
        0 if no drift detected, 1 otherwise.
    """
    try:
        cfg: Config = load(config_path)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 1

    try:
        source_profile = get_profile(cfg, args.source)
    except KeyError:
        print(f"Unknown profile: {args.source}", file=sys.stderr)
        return 1

    try:
        target_profile = get_profile(cfg, args.target)
    except KeyError:
        print(f"Unknown profile: {args.target}", file=sys.stderr)
        return 1

    try:
        with psycopg2.connect(source_profile.dsn) as src_conn:
            source_tables = fetch_schema(src_conn)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to connect to source '{args.source}': {exc}", file=sys.stderr)
        return 1

    try:
        with psycopg2.connect(target_profile.dsn) as tgt_conn:
            target_tables = fetch_schema(tgt_conn)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to connect to target '{args.target}': {exc}", file=sys.stderr)
        return 1

    report = compute_drift(
        source_tables,
        target_tables,
        source_env=args.source,
        target_env=args.target,
    )

    use_color = not getattr(args, "no_color", False)
    print(format_report(report, color=use_color))

    return 1 if report.has_drift else 0
