"""Identify tables and columns that change most frequently across audit history."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from pgdrift.audit import load_audit


@dataclass
class HotspotEntry:
    table: str
    change_count: int
    column_changes: Dict[str, int] = field(default_factory=dict)


@dataclass
class HotspotReport:
    entries: List[HotspotEntry] = field(default_factory=list)


def most_changed(report: HotspotReport, n: int = 5) -> List[HotspotEntry]:
    return sorted(report.entries, key=lambda e: e.change_count, reverse=True)[:n]


def as_dict(report: HotspotReport) -> dict:
    return {
        "entries": [
            {
                "table": e.table,
                "change_count": e.change_count,
                "column_changes": e.column_changes,
            }
            for e in report.entries
        ]
    }


def compute_hotspots(profile: str, snapshots_dir: str = ".") -> HotspotReport:
    records = load_audit(profile, snapshots_dir)
    table_counts: Dict[str, int] = {}
    column_counts: Dict[str, Dict[str, int]] = {}

    for entry in records:
        for td in entry.get("tables", []):
            tname = td.get("table", "")
            table_counts[tname] = table_counts.get(tname, 0) + 1
            if tname not in column_counts:
                column_counts[tname] = {}
            for cd in td.get("column_diffs", []):
                col = cd.get("column", "")
                column_counts[tname][col] = column_counts[tname].get(col, 0) + 1

    entries = [
        HotspotEntry(
            table=t,
            change_count=c,
            column_changes=column_counts.get(t, {}),
        )
        for t, c in table_counts.items()
    ]
    return HotspotReport(entries=entries)
