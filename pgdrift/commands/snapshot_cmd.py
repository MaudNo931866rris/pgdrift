"""CLI sub-command handlers for snapshot operations."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.snapshot import save_snapshot, load_snapshot
from pgdrift.diff import diff_schemas
from pgdrift.formatter import format_report


def cmd_capture(args) -> int:
    """Capture a schema snapshot from a live database profile."""
    try:
        cfg = load(args.config)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        profile = get_profile(cfg, args.profile)
    except KeyError:
        print(f"Error: unknown profile '{args.profile}'", file=sys.stderr)
        return 1

    out_path = Path(args.output)
    try:
        conn = psycopg2.connect(profile.dsn)
        try:
            tables = fetch_schema(conn)
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Error connecting to database: {exc}", file=sys.stderr)
        return 1

    save_snapshot(tables, out_path)
    print(f"Snapshot saved to {out_path} ({len(tables)} tables).")
    return 0


def cmd_compare_snapshot(args) -> int:
    """Compare a live profile against a saved snapshot file."""
    try:
        cfg = load(args.config)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        profile = get_profile(cfg, args.profile)
    except KeyError:
        print(f"Error: unknown profile '{args.profile}'", file=sys.stderr)
        return 1

    snap_path = Path(args.snapshot)
    try:
        snapshot_tables = load_snapshot(snap_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        conn = psycopg2.connect(profile.dsn)
        try:
            live_tables = fetch_schema(conn)
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"Error connecting to database: {exc}", file=sys.stderr)
        return 1

    report = diff_schemas(
        source=snapshot_tables,
        target=live_tables,
        source_env=str(snap_path.name),
        target_env=args.profile,
    )
    print(format_report(report))
    return 1 if report.has_drift else 0
