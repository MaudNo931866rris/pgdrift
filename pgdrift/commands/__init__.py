"""Register all CLI sub-commands."""

from pgdrift.commands import (
    baseline_cmd,
    diff_cmd,
    filter_cmd,
    history_cmd,
    ignore_cmd,
    lint_cmd,
    mask_cmd,
    plugin_cmd,
    redact_cmd,
    report_cmd,
    schedule_cmd,
    scorecard_cmd,
    snapshot_cmd,
    tag_cmd,
    threshold_cmd,
    watch_cmd,
)


def register_all(subparsers) -> None:
    """Attach every command group to *subparsers*."""
    baseline_cmd.register(subparsers)
    diff_cmd  # registered via cli.py directly
    filter_cmd.register(subparsers)
    history_cmd.register(subparsers)
    ignore_cmd.register(subparsers)
    lint_cmd.register(subparsers)
    mask_cmd.register(subparsers)
    plugin_cmd.register(subparsers)
    redact_cmd.register(subparsers)
    report_cmd.register(subparsers)
    schedule_cmd.register(subparsers)
    scorecard_cmd.register(subparsers)
    snapshot_cmd.register(subparsers)
    tag_cmd.register(subparsers)
    threshold_cmd.register(subparsers)
    watch_cmd.register(subparsers)
