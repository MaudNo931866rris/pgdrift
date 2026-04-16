"""Register all sub-commands."""
from __future__ import annotations


def register_all(subparsers) -> None:
    from pgdrift.commands import (
        diff_cmd,
        snapshot_cmd,
        report_cmd,
        watch_cmd,
        history_cmd,
        baseline_cmd,
        tag_cmd,
        lint_cmd,
        ignore_cmd,
        mask_cmd,
        redact_cmd,
        schedule_cmd,
        plugin_cmd,
        scorecard_cmd,
        filter_cmd,
        pin_cmd,
        threshold_cmd,
        compare_cmd,
    )

    diff_cmd.register(subparsers)
    snapshot_cmd.register(subparsers)
    report_cmd.register(subparsers)
    watch_cmd.register(subparsers)
    history_cmd.register(subparsers)
    baseline_cmd.register(subparsers)
    tag_cmd.register(subparsers)
    lint_cmd.register(subparsers)
    ignore_cmd.register(subparsers)
    mask_cmd.register(subparsers)
    redact_cmd.register(subparsers)
    schedule_cmd.register(subparsers)
    plugin_cmd.register(subparsers)
    scorecard_cmd.register(subparsers)
    filter_cmd.register(subparsers)
    pin_cmd.register(subparsers)
    threshold_cmd.register(subparsers)
    compare_cmd.register(subparsers)
