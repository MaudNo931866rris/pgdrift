"""Register all sub-commands."""
from __future__ import annotations
import argparse
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
    threshold_cmd,
    plugin_cmd,
    scorecard_cmd,
    filter_cmd,
    pin_cmd,
    compare_cmd,
    policy_cmd,
    similarity_cmd,
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
    threshold_cmd,
    plugin_cmd,
    scorecard_cmd,
    filter_cmd,
    pin_cmd,
    compare_cmd,
    policy_cmd,
    similarity_cmd,
]


def register_all(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    for mod in _MODULES:
        mod.register(sub)
