from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from pgdrift.trend import TrendReport, TrendPoint


@dataclass
class AnomalyEntry:
    snapshot: str
    changes: int
    delta: int
    z_score: float

    def as_dict(self) -> dict:
        return {
            "snapshot": self.snapshot,
            "changes": self.changes,
            "delta": self.delta,
            "z_score": round(self.z_score, 4),
        }


@dataclass
class AnomalyReport:
    entries: List[AnomalyEntry] = field(default_factory=list)

    def any_anomalies(self) -> bool:
        return len(self.entries) > 0

    def as_dict(self) -> dict:
        return {"anomalies": [e.as_dict() for e in self.entries]}


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


def detect_anomalies(trend: TrendReport, threshold: float = 2.0) -> AnomalyReport:
    points: List[TrendPoint] = trend.points
    if len(points) < 3:
        return AnomalyReport()

    changes = [float(p.total_changes) for p in points]
    mean = _mean(changes)
    std = _stddev(changes, mean)

    entries: List[AnomalyEntry] = []
    for i, p in enumerate(points):
        z = (p.total_changes - mean) / std if std > 0 else 0.0
        if abs(z) >= threshold:
            delta = p.total_changes - (points[i - 1].total_changes if i > 0 else 0)
            entries.append(AnomalyEntry(
                snapshot=p.label,
                changes=p.total_changes,
                delta=delta,
                z_score=z,
            ))

    return AnomalyReport(entries=entries)
