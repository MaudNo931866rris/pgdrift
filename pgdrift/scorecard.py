"""Drift scorecard: summarises a DriftReport into a numeric health score."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pgdrift.diff import DriftReport


@dataclass
class ScorecardResult:
    source: str
    target: str
    total_tables: int
    added_tables: int
    removed_tables: int
    modified_tables: int
    total_column_changes: int
    score: float  # 0.0 (worst) – 100.0 (perfect)
    grade: str

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "total_tables": self.total_tables,
            "added_tables": self.added_tables,
            "removed_tables": self.removed_tables,
            "modified_tables": self.modified_tables,
            "total_column_changes": self.total_column_changes,
            "score": round(self.score, 2),
            "grade": self.grade,
        }


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def compute_scorecard(report: DriftReport, total_tables: Optional[int] = None) -> ScorecardResult:
    """Compute a health score from *report*.

    *total_tables* is the reference table count (source side).  When omitted it
    is derived from the report itself.
    """
    added = len(report.added_tables)
    removed = len(report.removed_tables)
    modified = len(report.modified_tables)

    col_changes = sum(
        len(td.added_columns) + len(td.removed_columns) + len(td.modified_columns)
        for td in report.modified_tables
    )

    if total_tables is None:
        # source tables = modified + removed (tables that existed in source)
        total_tables = modified + removed + max(0, added == 0 and 1 or 0)
        # fall back: count all unique tables referenced
        total_tables = max(1, modified + removed)

    penalty = (added * 10) + (removed * 15) + (modified * 5) + (col_changes * 2)
    baseline = max(total_tables, 1) * 10
    raw = max(0.0, baseline - penalty) / baseline * 100.0
    score = min(100.0, raw)

    return ScorecardResult(
        source=report.source,
        target=report.target,
        total_tables=total_tables,
        added_tables=added,
        removed_tables=removed,
        modified_tables=modified,
        total_column_changes=col_changes,
        score=score,
        grade=_grade(score),
    )
