"""Schema churn: tracks how frequently tables/columns change over time."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pgdrift.audit import load_audit


@dataclass
class ChurnEntry:
    table: str
    change_count: int
    first_seen: str
    last_seen: str

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "change_count": self.change_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


@dataclass
class ChurnReport:
    entries: List[ChurnEntry] = field(default_factory=list)

    def most_churned(self, n: int = 5) -> List[ChurnEntry]:
        return sorted(self.entries, key=lambda e: e.change_count, reverse=True)[:n]

    def as_dict(self) -> dict:
        return {"entries": [e.as_dict() for e in self.entries]}


def compute_churn(profile: str, snapshot_dir: Optional[str] = None) -> ChurnReport:
    """Compute churn from audit history for a given profile."""
    records = load_audit(profile, snapshot_dir=snapshot_dir)
    if not records:
        return ChurnReport()

    counts: Dict[str, int] = {}
    first: Dict[str, str] = {}
    last: Dict[str, str] = {}

    for record in records:
        ts = record.get("captured_at", "")
        report = record.get("report", {})
        added = report.get("added_tables", [])
        removed = report.get("removed_tables", [])
        modified = report.get("modified_tables", [])

        for tname in added + removed + modified:
            counts[tname] = counts.get(tname, 0) + 1
            if tname not in first:
                first[tname] = ts
            last[tname] = ts

    entries = [
        ChurnEntry(
            table=t,
            change_count=counts[t],
            first_seen=first[t],
            last_seen=last[t],
        )
        for t in counts
    ]
    return ChurnReport(entries=entries)
