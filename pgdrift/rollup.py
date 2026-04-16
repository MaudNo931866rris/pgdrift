"""Rollup: aggregate multiple DriftReports into a combined summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pgdrift.diff import DriftReport, TableDiff


@dataclass
class RollupEntry:
    source: str
    target: str
    added_tables: int
    removed_tables: int
    modified_tables: int
    total_changes: int


@dataclass
class RollupReport:
    entries: List[RollupEntry] = field(default_factory=list)

    @property
    def total_reports(self) -> int:
        return len(self.entries)

    @property
    def grand_total_changes(self) -> int:
        return sum(e.total_changes for e in self.entries)

    @property
    def any_drift(self) -> bool:
        return self.grand_total_changes > 0


def _count_modified(diffs: List[TableDiff]) -> int:
    return sum(
        1 for d in diffs
        if not d.added and not d.removed and d.column_diffs
    )


def build_rollup(reports: List[DriftReport]) -> RollupReport:
    """Aggregate a list of DriftReports into a RollupReport."""
    entries: List[RollupEntry] = []
    for report in reports:
        added = sum(1 for d in report.table_diffs if d.added)
        removed = sum(1 for d in report.table_diffs if d.removed)
        modified = _count_modified(report.table_diffs)
        total = added + removed + modified
        entries.append(RollupEntry(
            source=report.source_env,
            target=report.target_env,
            added_tables=added,
            removed_tables=removed,
            modified_tables=modified,
            total_changes=total,
        ))
    return RollupReport(entries=entries)
