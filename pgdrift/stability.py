"""Schema stability scoring across audit history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.audit import load_audit


@dataclass
class StabilityEntry:
    table: str
    change_count: int
    snapshot_count: int
    stability_score: float  # 0.0 (volatile) – 1.0 (stable)

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "change_count": self.change_count,
            "snapshot_count": self.snapshot_count,
            "stability_score": round(self.stability_score, 4),
        }


@dataclass
class StabilityReport:
    entries: List[StabilityEntry] = field(default_factory=list)

    def most_stable(self, n: int = 5) -> List[StabilityEntry]:
        return sorted(self.entries, key=lambda e: e.stability_score, reverse=True)[:n]

    def least_stable(self, n: int = 5) -> List[StabilityEntry]:
        return sorted(self.entries, key=lambda e: e.stability_score)[:n]

    def average_score(self) -> float:
        if not self.entries:
            return 1.0
        return sum(e.stability_score for e in self.entries) / len(self.entries)

    def as_dict(self) -> dict:
        return {
            "average_score": round(self.average_score(), 4),
            "entries": [e.as_dict() for e in self.entries],
        }


def _score(change_count: int, snapshot_count: int) -> float:
    """Fraction of snapshots in which the table did NOT change."""
    if snapshot_count <= 0:
        return 1.0
    changed = min(change_count, snapshot_count)
    return 1.0 - (changed / snapshot_count)


def compute_stability(snapshot_dir: Optional[str] = None) -> StabilityReport:
    """Derive per-table stability from audit records."""
    records = load_audit(snapshot_dir)
    if not records:
        return StabilityReport()

    snapshot_count = len(records)
    change_counts: dict[str, int] = {}

    for record in records:
        seen: set[str] = set()
        for table_diff in record.get("tables", []):
            tname = table_diff.get("table", "")
            if tname and tname not in seen:
                change_counts[tname] = change_counts.get(tname, 0) + 1
                seen.add(tname)

    entries = [
        StabilityEntry(
            table=table,
            change_count=count,
            snapshot_count=snapshot_count,
            stability_score=_score(count, snapshot_count),
        )
        for table, count in sorted(change_counts.items())
    ]
    return StabilityReport(entries=entries)
