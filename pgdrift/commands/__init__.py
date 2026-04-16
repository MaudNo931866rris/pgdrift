"""Register all CLI sub-commands."""
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
    threshold_cmd,
    policy_cmd,
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
    threshold_cmd,
    policy_cmd,
]


def register_all(subparsers) -> None:
    for mod in _MODULES:
        if hasattr(mod, "register"):
            mod.register(subparsers)
