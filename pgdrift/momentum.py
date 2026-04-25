"""Momentum analysis: measures whether schema change rate is accelerating or decelerating."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.trend import TrendPoint


@dataclass
class MomentumPoint:
    timestamp: str
    changes: int
    delta: int  # change relative to previous point
    direction: str  # 'accelerating', 'decelerating', or 'stable'


@dataclass
class MomentumReport:
    points: List[MomentumPoint] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.points) == 0

    def is_accelerating(self) -> bool:
        """Return True if the most recent delta is positive."""
        if not self.points:
            return False
        return self.points[-1].direction == "accelerating"

    def is_decelerating(self) -> bool:
        """Return True if the most recent delta is negative."""
        if not self.points:
            return False
        return self.points[-1].direction == "decelerating"

    def average_delta(self) -> float:
        if len(self.points) < 2:
            return 0.0
        deltas = [p.delta for p in self.points[1:]]
        return sum(deltas) / len(deltas)

    def as_dict(self) -> dict:
        return {
            "points": [
                {
                    "timestamp": p.timestamp,
                    "changes": p.changes,
                    "delta": p.delta,
                    "direction": p.direction,
                }
                for p in self.points
            ],
            "average_delta": self.average_delta(),
            "is_accelerating": self.is_accelerating(),
            "is_decelerating": self.is_decelerating(),
        }


def _direction(delta: int) -> str:
    if delta > 0:
        return "accelerating"
    if delta < 0:
        return "decelerating"
    return "stable"


def compute_momentum(trend_points: List[TrendPoint]) -> MomentumReport:
    """Compute momentum from a list of TrendPoints ordered by time."""
    if not trend_points:
        return MomentumReport()

    points: List[MomentumPoint] = []
    for i, tp in enumerate(trend_points):
        if i == 0:
            delta = 0
        else:
            delta = tp.total_changes - trend_points[i - 1].total_changes
        points.append(
            MomentumPoint(
                timestamp=tp.timestamp,
                changes=tp.total_changes,
                delta=delta,
                direction=_direction(delta),
            )
        )
    return MomentumReport(points=points)
