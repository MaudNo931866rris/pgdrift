"""Fragility analysis: identifies tables most likely to break dependents on schema change."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from pgdrift.diff import DriftReport, TableDiff


@dataclass
class FragilityEntry:
    table: str
    change_count: int
    has_removals: bool
    has_type_changes: bool
    score: float

    def as_dict(self) -> Dict:
        return {
            "table": self.table,
            "change_count": self.change_count,
            "has_removals": self.has_removals,
            "has_type_changes": self.has_type_changes,
            "score": round(self.score, 3),
        }


@dataclass
class FragilityReport:
    entries: List[FragilityEntry] = field(default_factory=list)

    def most_fragile(self, n: int = 5) -> List[FragilityEntry]:
        return sorted(self.entries, key=lambda e: e.score, reverse=True)[:n]

    def any_fragile(self) -> bool:
        return any(e.score > 0 for e in self.entries)

    def as_dict(self) -> Dict:
        return {"entries": [e.as_dict() for e in self.entries]}


def _score_table_diff(td: TableDiff) -> FragilityEntry:
    removals = 0
    type_changes = 0
    total = 0

    for cd in td.column_diffs:
        total += 1
        if cd.change_type == "removed":
            removals += 1
        elif cd.change_type == "modified" and cd.source and cd.target:
            if cd.source.data_type != cd.target.data_type:
                type_changes += 1

    score = 0.0
    score += removals * 2.0
    score += type_changes * 1.5
    score += total * 0.1
    if td.status == "removed":
        score += 5.0

    return FragilityEntry(
        table=td.table,
        change_count=total,
        has_removals=removals > 0,
        has_type_changes=type_changes > 0,
        score=score,
    )


def compute_fragility(report: DriftReport) -> FragilityReport:
    entries: List[FragilityEntry] = []
    for td in report.table_diffs:
        entry = _score_table_diff(td)
        if entry.score > 0:
            entries.append(entry)
    return FragilityReport(entries=entries)
