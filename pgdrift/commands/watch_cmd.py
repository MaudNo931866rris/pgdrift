"""watch_cmd.py — periodically poll for schema drift and alert on changes."""

import time
import sys
from argparse import Namespace

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.diff import compute_drift
from pgdrift.formatter import format_report

_DEFAULT_INTERVAL = 60  # seconds


def cmd_watch(args: Namespace) -> int:
    """Continuously compare source and target schemas at a fixed interval.

    Returns 0 when interrupted (KeyboardInterrupt), non-zero on setup error.
    """
    try:
        config = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    try:
        source_profile = get_profile(config, args.source)
    except KeyError:
        print(f"Unknown profile: {args.source}", file=sys.stderr)
        return 1

    try:
        target_profile = get_profile(config, args.target)
    except KeyError:
        print(f"Unknown profile: {args.target}", file=sys.stderr)
        return 1

    interval = getattr(args, "interval", _DEFAULT_INTERVAL)
    print(
        f"Watching for drift between '{args.source}' and '{args.target}' "
        f"every {interval}s. Press Ctrl+C to stop."
    )

    import psycopg2

    try:
        while True:
            try:
                with psycopg2.connect(source_profile.dsn) as src_conn:
                    source_tables = fetch_schema(src_conn)
                with psycopg2.connect(target_profile.dsn) as tgt_conn:
                    target_tables = fetch_schema(tgt_conn)
            except Exception as exc:  # noqa: BLE001
                print(f"Connection error: {exc}", file=sys.stderr)
                time.sleep(interval)
                continue

            report = compute_drift(args.source, args.target, source_tables, target_tables)
            if report.has_drift:
                print("[DRIFT DETECTED]")
                print(format_report(report))
            else:
                print("[OK] No drift detected.")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch stopped.")
        return 0


def register(subparsers) -> None:  # noqa: ANN001
    """Register the 'watch' subcommand."""
    parser = subparsers.add_parser(
        "watch",
        help="Continuously monitor schema drift between two environments.",
    )
    parser.add_argument("source", help="Source profile name.")
    parser.add_argument("target", help="Target profile name.")
    parser.add_argument(
        "--interval",
        type=int,
        default=_DEFAULT_INTERVAL,
        metavar="SECONDS",
        help=f"Poll interval in seconds (default: {_DEFAULT_INTERVAL}).",
    )
    parser.add_argument(
        "--config",
        default="pgdrift.yml",
        help="Path to config file (default: pgdrift.yml).",
    )
    parser.set_defaults(func=cmd_watch)
