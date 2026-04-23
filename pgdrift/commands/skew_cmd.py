"""CLI command: pgdrift skew — report column-count skew across schema tables."""
from __future__ import annotations

import argparse
import json

from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.skew import compute_skew, as_dict


def cmd_skew(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        return 1

    profile = get_profile(cfg, args.profile)
    if profile is None:
        print(f"Unknown profile: {args.profile}")
        return 1

    import psycopg2

    conn = psycopg2.connect(profile.dsn)
    try:
        tables = fetch_schema(conn)
    finally:
        conn.close()

    report = compute_skew(tables)
    threshold = args.threshold

    if args.json:
        output = {
            "mean_columns": report.mean_columns,
            "stddev": report.stddev,
            "outliers": [as_dict(e) for e in report.outliers(threshold)],
            "all": [as_dict(e) for e in report.entries],
        }
        print(json.dumps(output, indent=2))
        return 0

    if not report.entries:
        print("No tables found.")
        return 0

    print(f"Schema skew report  (mean={report.mean_columns} cols, stddev={report.stddev})")
    print(f"Threshold: ±{threshold} stddev\n")

    outliers = report.outliers(threshold)
    if not outliers:
        print("No skewed tables detected.")
        return 0

    print(f"{'Table':<40} {'Columns':>8} {'Deviation':>10}")
    print("-" * 62)
    for entry in outliers:
        print(f"{entry.table:<40} {entry.column_count:>8} {entry.deviation:>10.2f}")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("skew", help="Detect tables with unusual column counts")
    p.add_argument("profile", help="Database profile name")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--threshold", type=float, default=2.0,
                   help="Stddev threshold for outlier detection (default: 2.0)")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_skew)
