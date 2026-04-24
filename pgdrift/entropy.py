from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

from pgdrift.trend import TrendPoint


@dataclass
class EntropyPoint:
    timestamp: str
    total_changes: int
    entropy: float

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total_changes": self.total_changes,
            "entropy": self.entropy,
        }


@dataclass
class EntropyReport:
    points: List[EntropyPoint] = field(default_factory=list)

    def average_entropy(self) -> float:
        if not self.points:
            return 0.0
        return sum(p.entropy for p in self.points) / len(self.points)

    def max_entropy(self) -> float:
        if not self.points:
            return 0.0
        return max(p.entropy for p in self.points)

    def as_dict(self) -> dict:
        return {
            "average_entropy": self.average_entropy(),
            "max_entropy": self.max_entropy(),
            "points": [p.as_dict() for p in self.points],
        }


def _shannon_entropy(values: List[int]) -> float:
    """Compute Shannon entropy over a list of non-negative integer counts."""
    total = sum(values)
    if total == 0:
        return 0.0
    result = 0.0
    for v in values:
        if v > 0:
            p = v / total
            result -= p * math.log2(p)
    return result


def _entropy_for_point(pt: TrendPoint) -> float:
    counts = [
        pt.added_tables,
        pt.removed_tables,
        pt.modified_tables,
    ]
    return _shannon_entropy(counts)


def compute_entropy(points: List[TrendPoint]) -> EntropyReport:
    """Build an EntropyReport from a sequence of TrendPoints."""
    entropy_points = [
        EntropyPoint(
            timestamp=pt.timestamp,
            total_changes=pt.added_tables + pt.removed_tables + pt.modified_tables,
            entropy=_entropy_for_point(pt),
        )
        for pt in points
    ]
    return EntropyReport(points=entropy_points)
