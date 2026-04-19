"""Shadow schema tracking: detect when a table's schema silently diverges from a pinned reference."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pgdrift.diff import DriftReport, TableDiff
from pgdrift.pin import load_pin_tables
from pgdrift.diff import diff_report


@dataclass
class ShadowEntry:
    table: str
    pin_label: str
    drift: TableDiff


@dataclass
class ShadowReport:
    entries: List[ShadowEntry] = field(default_factory=list)

    def any_shadow(self) -> bool:
        return len(self.entries) > 0

    def as_dict(self) -> dict:
        return {
            "any_shadow": self.any_shadow(),
            "count": len(self.entries),
            "entries": [
                {
                    "table": e.table,
                    "pin_label": e.pin_label,
                    "added_columns": [c.name for c in e.drift.added_columns],
                    "removed_columns": [c.name for c in e.drift.removed_columns],
                    "modified_columns": [c.name for c in e.drift.modified_columns],
                }
                for e in self.entries
            ],
        }


def compute_shadow(pin_label: str, live_tables: Dict) -> ShadowReport:
    """Compare live schema tables against a saved pin."""
    pinned = load_pin_tables(pin_label)
    if pinned is None:
        return ShadowReport()

    report = diff_report(pinned, live_tables, source=pin_label, target="live")
    entries: List[ShadowEntry] = []
    for td in report.table_diffs:
        if td.added_columns or td.removed_columns or td.modified_columns:
            entries.append(ShadowEntry(table=td.name, pin_label=pin_label, drift=td))
    return ShadowReport(entries=entries)
