"""Register all sub-commands."""
from __future__ import annotations

import argparse

from pgdrift.commands import (
    baseline_cmd,
    diff_cmd,
    filter_cmd,
    history_cmd,
    ignore_cmd,
    impact_cmd,
    lint_cmd,
    mask_cmd,
    pin_cmd,
    plugin_cmd,
    policy_cmd,
    redact_cmd,
    report_cmd,
    revert_cmd,
    schedule_cmd,
    scorecard_cmd,
    similarity_cmd,
    snapshot_cmd,
    stale_cmd,
    tag_cmd,
    threshold_cmd,
    watch_cmd,
    compare_cmd,
)

_MODULES = [
    baseline_cmd,
    diff_cmd,
    filter_cmd,
    history_cmd,
    ignore_cmd,
    impact_cmd,
    lint_cmd,
    mask_cmd,
    pin_cmd,
    plugin_cmd,
    policy_cmd,
    redact_cmd,
    report_cmd,
    revert_cmd,
    schedule_cmd,
    scorecard_cmd,
    similarity_cmd,
    snapshot_cmd,
    stale_cmd,
    tag_cmd,
    threshold_cmd,
    watch_cmd,
    compare_cmd,
]


def register_all(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    for mod in _MODULES:
        mod.register(subparsers)
