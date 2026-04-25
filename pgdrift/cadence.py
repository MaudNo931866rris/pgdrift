"""Cadence analysis: measures how regularly schema changes occur across audit history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import List, Optional


@dataclass
class CadenceEntry:
    profile: str
    interval_days: float  # days between consecutive snapshots
    captured_at: str


@dataclass
class CadenceReport:
    entries: List[CadenceEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def average_interval(self) -> float:
        if not self.entries:
            return 0.0
        return mean(e.interval_days for e in self.entries)

    def stddev_interval(self) -> float:
        if len(self.entries) < 2:
            return 0.0
        return stdev(e.interval_days for e in self.entries)

    def is_regular(self, tolerance: float = 1.0) -> bool:
        """Return True if stddev of intervals is within *tolerance* days."""
        return self.stddev_interval() <= tolerance

    def as_dict(self) -> dict:
        return {
            "average_interval_days": round(self.average_interval(), 4),
            "stddev_interval_days": round(self.stddev_interval(), 4),
            "is_regular": self.is_regular(),
            "entries": [
                {"profile": e.profile, "interval_days": e.interval_days, "captured_at": e.captured_at}
                for e in self.entries
            ],
        }


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def compute_cadence(audit_records: list) -> CadenceReport:
    """Build a CadenceReport from a list of audit records (dicts with 'captured_at' and 'profile')."""
    if not audit_records:
        return CadenceReport()

    sorted_records = sorted(audit_records, key=lambda r: r.get("captured_at", ""))
    entries: List[CadenceEntry] = []

    for i in range(1, len(sorted_records)):
        prev = sorted_records[i - 1]
        curr = sorted_records[i]
        try:
            t0 = _parse_ts(prev["captured_at"])
            t1 = _parse_ts(curr["captured_at"])
            interval = (t1 - t0).total_seconds() / 86400.0
            entries.append(
                CadenceEntry(
                    profile=curr.get("profile", ""),
                    interval_days=round(interval, 4),
                    captured_at=curr["captured_at"],
                )
            )
        except (KeyError, ValueError):
            continue

    return CadenceReport(entries=entries)
