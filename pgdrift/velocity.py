"""Drift velocity: rate of change per day across audit history."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone

from pgdrift.audit import load_audit


@dataclass
class VelocityPoint:
    captured_at: str
    changes: int


@dataclass
class VelocityReport:
    points: List[VelocityPoint] = field(default_factory=list)

    def average_per_day(self) -> float:
        if len(self.points) < 2:
            return 0.0
        try:
            t0 = datetime.fromisoformat(self.points[0].captured_at).replace(tzinfo=timezone.utc)
            t1 = datetime.fromisoformat(self.points[-1].captured_at).replace(tzinfo=timezone.utc)
            days = max((t1 - t0).total_seconds() / 86400, 1)
        except ValueError:
            days = 1.0
        total = sum(p.changes for p in self.points)
        return round(total / days, 4)

    def peak(self) -> Optional[VelocityPoint]:
        if not self.points:
            return None
        return max(self.points, key=lambda p: p.changes)

    def as_dict(self) -> dict:
        return {
            "average_per_day": self.average_per_day(),
            "peak": {"captured_at": self.peak().captured_at, "changes": self.peak().changes} if self.peak() else None,
            "points": [{"captured_at": p.captured_at, "changes": p.changes} for p in self.points],
        }


def compute_velocity(snapshot_dir: str) -> VelocityReport:
    records = load_audit(snapshot_dir)
    points = [
        VelocityPoint(
            captured_at=r.get("captured_at", ""),
            changes=(
                len(r.get("added_tables", []))
                + len(r.get("removed_tables", []))
                + len(r.get("modified_tables", []))
            ),
        )
        for r in records
    ]
    points.sort(key=lambda p: p.captured_at)
    return VelocityReport(points=points)
