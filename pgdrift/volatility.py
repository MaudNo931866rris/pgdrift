"""Volatility analysis: measures how frequently each table's schema changes over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.audit import load_audit


@dataclass
class VolatilityEntry:
    table: str
    change_count: int
    snapshots_seen: int
    volatility_score: float  # change_count / snapshots_seen, 0.0-1.0

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "change_count": self.change_count,
            "snapshots_seen": self.snapshots_seen,
            "volatility_score": round(self.volatility_score, 4),
        }


@dataclass
class VolatilityReport:
    entries: List[VolatilityEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def most_volatile(self, n: int = 5) -> List[VolatilityEntry]:
        return sorted(self.entries, key=lambda e: e.volatility_score, reverse=True)[:n]

    def least_volatile(self, n: int = 5) -> List[VolatilityEntry]:
        return sorted(self.entries, key=lambda e: e.volatility_score)[:n]

    def average_score(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.volatility_score for e in self.entries) / len(self.entries)

    def as_dict(self) -> dict:
        return {
            "average_volatility_score": round(self.average_score(), 4),
            "entries": [e.as_dict() for e in self.entries],
        }


def compute_volatility(audit_dir: Optional[str] = None) -> VolatilityReport:
    """Compute per-table volatility from audit history."""
    records = load_audit(audit_dir)
    if not records:
        return VolatilityReport()

    table_changes: dict[str, int] = {}
    table_snapshots: dict[str, set] = {}

    for record in records:
        snapshot_id = record.get("captured_at", "")
        report = record.get("report")
        if not report:
            continue
        for td in report.get("tables", []):
            tname = td.get("table", "")
            if not tname:
                continue
            status = td.get("status", "unchanged")
            if tname not in table_snapshots:
                table_snapshots[tname] = set()
                table_changes[tname] = 0
            table_snapshots[tname].add(snapshot_id)
            if status != "unchanged":
                table_changes[tname] += 1

    entries = []
    for table, seen in table_snapshots.items():
        count = table_changes.get(table, 0)
        seen_count = len(seen)
        score = count / seen_count if seen_count > 0 else 0.0
        entries.append(VolatilityEntry(
            table=table,
            change_count=count,
            snapshots_seen=seen_count,
            volatility_score=score,
        ))

    entries.sort(key=lambda e: e.volatility_score, reverse=True)
    return VolatilityReport(entries=entries)
