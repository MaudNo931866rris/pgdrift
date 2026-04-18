"""Tests for pgdrift.variance."""
from __future__ import annotations
from pgdrift.trend import TrendReport, TrendPoint
from pgdrift.variance import VariancePoint, VarianceReport, compute_variance


def _trend(*counts: tuple) -> TrendReport:
    """Build a TrendReport from (added, removed, modified) tuples."""
    points = [
        TrendPoint(
            captured_at=f"2024-01-0{i+1}T00:00:00",
            added_tables=a,
            removed_tables=r,
            modified_tables=m,
        )
        for i, (a, r, m) in enumerate(counts)
    ]
    return TrendReport(points=points)


def test_empty_trend_returns_empty_variance():
    report = compute_variance(TrendReport(points=[]))
    assert report.points == []
    assert report.is_stable
    assert report.max_delta == 0
    assert report.mean_changes == 0.0


def test_single_point_has_zero_delta():
    trend = _trend((2, 1, 0))
    report = compute_variance(trend)
    assert len(report.points) == 1
    assert report.points[0].delta == 0
    assert report.points[0].total_changes == 3


def test_stable_when_all_deltas_zero():
    trend = _trend((1, 0, 0), (1, 0, 0), (1, 0, 0))
    report = compute_variance(trend)
    assert report.is_stable


def test_not_stable_when_delta_nonzero():
    trend = _trend((0, 0, 0), (2, 1, 0))
    report = compute_variance(trend)
    assert not report.is_stable
    assert report.points[1].delta == 3


def test_max_delta_picks_largest_absolute():
    trend = _trend((0, 0, 0), (5, 0, 0), (0, 0, 0))
    report = compute_variance(trend)
    assert report.max_delta == 5


def test_mean_changes_is_average():
    trend = _trend((2, 0, 0), (4, 0, 0))
    report = compute_variance(trend)
    assert report.mean_changes == 3.0


def test_as_dict_structure():
    trend = _trend((1, 1, 1))
    d = compute_variance(trend).as_dict()
    assert "is_stable" in d
    assert "max_delta" in d
    assert "mean_changes" in d
    assert isinstance(d["points"], list)
    assert d["points"][0]["total_changes"] == 3
