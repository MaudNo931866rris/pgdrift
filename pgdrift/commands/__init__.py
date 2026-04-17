"""Register all sub-commands with the top-level argument parser."""
from pgdrift.commands import (
    snapshot_cmd,
    diff_cmd,
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
    compare_cmd,
    policy_cmd,
    similarity_cmd,
    threshold_cmd,
    revert_cmd,
)

_MODULES = [
    snapshot_cmd,
    diff_cmd,
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
    compare_cmd,
    policy_cmd,
    similarity_cmd,
    threshold_cmd,
    revert_cmd,
]


def register_all(subparsers) -> None:
    for mod in _MODULES:
        mod.register(subparsers)
