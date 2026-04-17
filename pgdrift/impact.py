"""Estimate the impact severity of detected schema drift."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from pgdrift.diff import DriftReport, TableDiff


@dataclass
class ImpactItem:
    table: str
    change_type: str  # added, removed, modified
    severity: str     # low, medium, high, critical
    reason: str


@dataclass
class ImpactReport:
    items: List[ImpactItem] = field(default_factory=list)

    def critical(self) -> List[ImpactItem]:
        return [i for i in self.items if i.severity == "critical"]

    def high(self) -> List[ImpactItem]:
        return [i for i in self.items if i.severity == "high"]

    def as_dict(self) -> dict:
        return {
            "items": [
                {"table": i.table, "change_type": i.change_type,
                 "severity": i.severity, "reason": i.reason}
                for i in self.items
            ],
            "critical_count": len(self.critical()),
            "high_count": len(self.high()),
        }


def _severity_for_table_diff(td: TableDiff) -> ImpactItem:
    name = td.table_name
    if td.removed:
        return ImpactItem(name, "removed", "critical", "Table dropped; dependent queries will break")
    if td.added:
        return ImpactItem(name, "added", "low", "New table introduced")
    # modified
    dropped_cols = [c for c in td.column_diffs if c.removed]
    type_changes = [c for c in td.column_diffs if c.type_changed]
    if dropped_cols:
        return ImpactItem(name, "modified", "high",
                          f"{len(dropped_cols)} column(s) dropped")
    if type_changes:
        return ImpactItem(name, "modified", "medium",
                          f"{len(type_changes)} column type(s) changed")
    return ImpactItem(name, "modified", "low", "Non-breaking column changes")


def compute_impact(report: DriftReport) -> ImpactReport:
    items = [_severity_for_table_diff(td) for td in report.table_diffs]
    return ImpactReport(items=items)
