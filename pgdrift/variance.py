"""Variance tracking: measure how much schema drift changes over time."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pgdrift.drift_age import DriftAgeReport
from pgdrift.trend import TrendReport, TrendPoint


@dataclass
class VariancePoint:
    label: str
    total_changes: int
    delta: int  # change vs previous point


@dataclass
class VarianceReport:
    points: List[VariancePoint] = field(default_factory=list)

    @property
    def is_stable(self) -> bool:
        return all(p.delta == 0 for p in self.points)

    @property
    def max_delta(self) -> int:
        if not self.points:
            return 0
        return max(abs(p.delta) for p in self.points)

    @property
    def mean_changes(self) -> float:
        if not self.points:
            return 0.0
        return sum(p.total_changes for p in self.points) / len(self.points)

    def as_dict(self) -> dict:
        return {
            "is_stable": self.is_stable,
            "max_delta": self.max_delta,
            "mean_changes": round(self.mean_changes, 2),
            "points": [
                {"label": p.label, "total_changes": p.total_changes, "delta": p.delta}
                for p in self.points
            ],
        }


def compute_variance(trend: TrendReport) -> VarianceReport:
    """Derive a VarianceReport from a TrendReport."""
    points: List[VariancePoint] = []
    prev: Optional[int] = None
    for tp in trend.points:
        total = tp.added_tables + tp.removed_tables + tp.modified_tables
        delta = 0 if prev is None else total - prev
        points.append(VariancePoint(label=tp.captured_at, total_changes=total, delta=delta))
        prev = total
    return VarianceReport(points=points)
