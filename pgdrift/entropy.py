"""Schema entropy: measures how unpredictable/varied a schema is over time."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.audit import load_audit


@dataclass
class EntropyPoint:
    snapshot_id: str
    captured_at: str
    changes: int
    entropy: float


@dataclass
class EntropyReport:
    points: List[EntropyPoint] = field(default_factory=list)

    def average_entropy(self) -> float:
        if not self.points:
            return 0.0
        return sum(p.entropy for p in self.points) / len(self.points)

    def max_entropy(self) -> Optional[EntropyPoint]:
        if not self.points:
            return None
        return max(self.points, key=lambda p: p.entropy)

    def as_dict(self) -> dict:
        return {
            "average_entropy": round(self.average_entropy(), 4),
            "max_entropy": self.max_entropy().entropy if self.max_entropy() else 0.0,
            "points": [
                {
                    "snapshot_id": p.snapshot_id,
                    "captured_at": p.captured_at,
                    "changes": p.changes,
                    "entropy": round(p.entropy, 4),
                }
                for p in self.points
            ],
        }


def _shannon_entropy(changes: int, total: int) -> float:
    if total == 0 or changes == 0:
        return 0.0
    p = changes / total
    return -p * math.log2(p)


def compute_entropy(directory: str) -> EntropyReport:
    records = load_audit(directory)
    if not records:
        return EntropyReport()

    total = sum(r.get("total_changes", 0) for r in records)
    points = []
    for r in records:
        changes = r.get("total_changes", 0)
        entropy = _shannon_entropy(changes, total) if total > 0 else 0.0
        points.append(
            EntropyPoint(
                snapshot_id=r.get("snapshot_id", ""),
                captured_at=r.get("captured_at", ""),
                changes=changes,
                entropy=entropy,
            )
        )
    return EntropyReport(points=points)
