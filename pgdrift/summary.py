"""Generates a concise drift summary with counts and severity classification."""

from dataclasses import dataclass
from typing import List

from pgdrift.diff import DriftReport, TableDiff


@dataclass
class DriftSummary:
    source: str
    target: str
    added_tables: int
    removed_tables: int
    modified_tables: int
    added_columns: int
    removed_columns: int
    modified_columns: int
    severity: str  # "none", "low", "medium", "high"

    @property
    def total_changes(self) -> int:
        return (
            self.added_tables
            + self.removed_tables
            + self.modified_tables
            + self.added_columns
            + self.removed_columns
            + self.modified_columns
        )

    @property
    def has_destructive_changes(self) -> bool:
        """Return True if any tables or columns were removed."""
        return self.removed_tables > 0 or self.removed_columns > 0


def _severity(summary: "DriftSummary") -> str:
    total = summary.total_changes
    if total == 0:
        return "none"
    if summary.has_destructive_changes:
        return "high"
    if total >= 10:
        return "medium"
    return "low"


def _count_column_changes(tables: List[TableDiff]):
    added = removed = modified = 0
    for t in tables:
        added += len(t.added_columns)
        removed += len(t.removed_columns)
        modified += len(t.modified_columns)
    return added, removed, modified


def compute_summary(report: DriftReport) -> DriftSummary:
    """Compute a DriftSummary from a DriftReport."""
    col_added, col_removed, col_modified = _count_column_changes(
        report.modified_tables
    )
    summary = DriftSummary(
        source=report.source,
        target=report.target,
        added_tables=len(report.added_tables),
        removed_tables=len(report.removed_tables),
        modified_tables=len(report.modified_tables),
        added_columns=col_added,
        removed_columns=col_removed,
        modified_columns=col_modified,
        severity="none",
    )
    summary.severity = _severity(summary)
    return summary


def format_summary(summary: DriftSummary) -> str:
    """Return a human-readable one-block summary string."""
    lines = [
        f"Drift Summary: {summary.source} \u2192 {summary.target}",
        f"  Severity  : {summary.severity.upper()}",
        f"  Tables    : +{summary.added_tables} added  "
        f"-{summary.removed_tables} removed  "
        f"~{summary.modified_tables} modified",
        f"  Columns   : +{summary.added_columns} added  "
        f"-{summary.removed_columns} removed  "
        f"~{summary.modified_columns} modified",
        f"  Total     : {summary.total_changes} change(s)",
    ]
    return "\n".join(lines)
