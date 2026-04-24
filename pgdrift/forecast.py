"""Forecast future schema drift based on historical audit data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.audit import load_audit
from pgdrift.trend import TrendPoint, _point_from_report


@dataclass
class ForecastPoint:
    period: str          # e.g. "week+1", "week+2"
    predicted_changes: float
    lower_bound: float
    upper_bound: float

    def as_dict(self) -> dict:
        return {
            "period": self.period,
            "predicted_changes": round(self.predicted_changes, 2),
            "lower_bound": round(self.lower_bound, 2),
            "upper_bound": round(self.upper_bound, 2),
        }


@dataclass
class ForecastReport:
    profile: str
    history: List[TrendPoint] = field(default_factory=list)
    forecast: List[ForecastPoint] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.forecast) == 0

    def as_dict(self) -> dict:
        return {
            "profile": self.profile,
            "history": [p.__dict__ for p in self.history],
            "forecast": [f.as_dict() for f in self.forecast],
        }


def _moving_average(values: List[float], window: int) -> float:
    if not values:
        return 0.0
    subset = values[-window:]
    return sum(subset) / len(subset)


def _std_dev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


def build_forecast(
    profile: str,
    snapshot_dir: str = "snapshots",
    horizons: int = 4,
    window: int = 3,
) -> ForecastReport:
    """Build a simple moving-average forecast over *horizons* future periods."""
    records = load_audit(snapshot_dir)
    points: List[TrendPoint] = []
    for entry in records:
        try:
            p = _point_from_report(entry["report"], entry.get("captured_at", ""))
            points.append(p)
        except Exception:
            continue

    change_counts = [float(p.total_changes) for p in points]
    forecast_points: List[ForecastPoint] = []
    base = _moving_average(change_counts, window)
    sigma = _std_dev(change_counts)

    for i in range(1, horizons + 1):
        fp = ForecastPoint(
            period=f"week+{i}",
            predicted_changes=base,
            lower_bound=max(0.0, base - sigma),
            upper_bound=base + sigma,
        )
        forecast_points.append(fp)

    return ForecastReport(profile=profile, history=points, forecast=forecast_points)
