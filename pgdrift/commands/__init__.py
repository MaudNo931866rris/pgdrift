"""Command registry for pgdrift CLI."""
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
    threshold_cmd,
    scorecard_cmd,
)

ALL_COMMANDS = [
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
    threshold_cmd,
    scorecard_cmd,
]


def register_all(subparsers) -> None:
    """Register every command module with *subparsers*."""
    for mod in ALL_COMMANDS:
        mod.register(subparsers)
