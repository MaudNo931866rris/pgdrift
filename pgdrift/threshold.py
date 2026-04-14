"""Drift threshold configuration and evaluation.

Allows users to define acceptable drift thresholds (e.g. max added/removed
tables or columns) and evaluate whether a DriftReport exceeds them.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

from pgdrift.diff import DriftReport

_THRESHOLD_FILE = ".pgdrift_threshold.json"


@dataclass
class ThresholdConfig:
    max_added_tables: Optional[int] = None
    max_removed_tables: Optional[int] = None
    max_modified_tables: Optional[int] = None
    max_added_columns: Optional[int] = None
    max_removed_columns: Optional[int] = None


@dataclass
class ThresholdResult:
    passed: bool
    violations: list[str]


def _threshold_path(directory: str = ".") -> str:
    return os.path.join(directory, _THRESHOLD_FILE)


def load_threshold(directory: str = ".") -> ThresholdConfig:
    path = _threshold_path(directory)
    if not os.path.exists(path):
        return ThresholdConfig()
    with open(path) as fh:
        data = json.load(fh)
    return ThresholdConfig(**{k: v for k, v in data.items() if k in ThresholdConfig.__dataclass_fields__})


def save_threshold(config: ThresholdConfig, directory: str = ".") -> None:
    path = _threshold_path(directory)
    with open(path, "w") as fh:
        json.dump(asdict(config), fh, indent=2)


def evaluate(report: DriftReport, config: ThresholdConfig) -> ThresholdResult:
    violations: list[str] = []

    added_tables = len(report.added_tables)
    removed_tables = len(report.removed_tables)
    modified_tables = len(report.modified_tables)

    added_cols = sum(len(t.added_columns) for t in report.modified_tables)
    removed_cols = sum(len(t.removed_columns) for t in report.modified_tables)

    checks = [
        (config.max_added_tables, added_tables, "added tables"),
        (config.max_removed_tables, removed_tables, "removed tables"),
        (config.max_modified_tables, modified_tables, "modified tables"),
        (config.max_added_columns, added_cols, "added columns"),
        (config.max_removed_columns, removed_cols, "removed columns"),
    ]

    for limit, actual, label in checks:
        if limit is not None and actual > limit:
            violations.append(
                f"{label}: {actual} exceeds threshold of {limit}"
            )

    return ThresholdResult(passed=len(violations) == 0, violations=violations)
