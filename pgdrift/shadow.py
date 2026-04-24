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

    def tables_with_shadow(self) -> List[str]:
        """Return a sorted list of table names that have detected drift."""
        return sorted(e.table for e in self.entries)


def compute_shadow(pin_label: str, live_tables: Dict) -> ShadowReport:
    """Compare live schema tables against a saved pin.

    Args:
        pin_label: The label identifying the pinned schema snapshot to compare against.
        live_tables: A mapping of table names to their current live schema definitions.

    Returns:
        A ShadowReport containing one entry per table whose live schema differs
        from the pinned reference. Returns an empty ShadowReport if the pin
        cannot be found.
    """
    pinned = load_pin_tables(pin_label)
    if pinned is None:
        return ShadowReport()

    report = diff_report(pinned, live_tables, source=pin_label, target="live")
    entries: List[ShadowEntry] = []
    for td in report.table_diffs:
        if td.added_columns or td.removed_columns or td.modified_columns:
            entries.append(ShadowEntry(table=td.name, pin_label=pin_label, drift=td))
    return ShadowReport(entries=entries)
