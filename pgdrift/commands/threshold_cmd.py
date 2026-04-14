"""CLI commands for managing drift thresholds."""

from __future__ import annotations

import argparse
import json

from pgdrift.threshold import ThresholdConfig, load_threshold, save_threshold


def cmd_threshold_set(args: argparse.Namespace) -> int:
    config = load_threshold()
    fields = [
        ("max_added_tables", args.max_added_tables),
        ("max_removed_tables", args.max_removed_tables),
        ("max_modified_tables", args.max_modified_tables),
        ("max_added_columns", args.max_added_columns),
        ("max_removed_columns", args.max_removed_columns),
    ]
    updated = False
    for field, value in fields:
        if value is not None:
            setattr(config, field, value)
            updated = True

    if not updated:
        print("No threshold values provided. Use --max-added-tables etc.")
        return 1

    save_threshold(config)
    print("Threshold saved.")
    return 0


def cmd_threshold_show(args: argparse.Namespace) -> int:
    config = load_threshold()
    data = {
        "max_added_tables": config.max_added_tables,
        "max_removed_tables": config.max_removed_tables,
        "max_modified_tables": config.max_modified_tables,
        "max_added_columns": config.max_added_columns,
        "max_removed_columns": config.max_removed_columns,
    }
    print(json.dumps(data, indent=2))
    return 0


def cmd_threshold_clear(args: argparse.Namespace) -> int:
    save_threshold(ThresholdConfig())
    print("Threshold cleared.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("threshold", help="Manage drift thresholds")
    sub = p.add_subparsers(dest="threshold_cmd")

    p_set = sub.add_parser("set", help="Set threshold values")
    p_set.add_argument("--max-added-tables", type=int, default=None)
    p_set.add_argument("--max-removed-tables", type=int, default=None)
    p_set.add_argument("--max-modified-tables", type=int, default=None)
    p_set.add_argument("--max-added-columns", type=int, default=None)
    p_set.add_argument("--max-removed-columns", type=int, default=None)
    p_set.set_defaults(func=cmd_threshold_set)

    p_show = sub.add_parser("show", help="Show current thresholds")
    p_show.set_defaults(func=cmd_threshold_show)

    p_clear = sub.add_parser("clear", help="Clear all thresholds")
    p_clear.set_defaults(func=cmd_threshold_clear)
