"""Tests for pgdrift.momentum."""
from __future__ import annotations

import pytest

from pgdrift.trend import TrendPoint
from pgdrift.momentum import (
    MomentumPoint,
    MomentumReport,
    compute_momentum,
    _direction,
)


def _point(ts: str, total: int) -> TrendPoint:
    return TrendPoint(timestamp=ts, total_changes=total)


# ---------------------------------------------------------------------------
# _direction
# ---------------------------------------------------------------------------

def test_direction_positive_is_accelerating():
    assert _direction(3) == "accelerating"


def test_direction_negative_is_decelerating():
    assert _direction(-2) == "decelerating"


def test_direction_zero_is_stable():
    assert _direction(0) == "stable"


# ---------------------------------------------------------------------------
# compute_momentum
# ---------------------------------------------------------------------------

def test_empty_trend_returns_empty_report():
    report = compute_momentum([])
    assert report.is_empty()


def test_single_point_has_zero_delta():
    report = compute_momentum([_point("2024-01-01", 5)])
    assert len(report.points) == 1
    assert report.points[0].delta == 0
    assert report.points[0].direction == "stable"


def test_increasing_changes_are_accelerating():
    points = [
        _point("2024-01-01", 2),
        _point("2024-01-02", 5),
    ]
    report = compute_momentum(points)
    assert report.points[1].delta == 3
    assert report.points[1].direction == "accelerating"
    assert report.is_accelerating()


def test_decreasing_changes_are_decelerating():
    points = [
        _point("2024-01-01", 8),
        _point("2024-01-02", 3),
    ]
    report = compute_momentum(points)
    assert report.points[1].delta == -5
    assert report.points[1].direction == "decelerating"
    assert report.is_decelerating()


def test_average_delta_calculated_correctly():
    points = [
        _point("2024-01-01", 0),
        _point("2024-01-02", 4),
        _point("2024-01-03", 6),
    ]
    report = compute_momentum(points)
    # deltas are 4 and 2 -> average 3.0
    assert report.average_delta() == pytest.approx(3.0)


def test_as_dict_contains_expected_keys():
    report = compute_momentum([_point("2024-01-01", 1), _point("2024-01-02", 3)])
    d = report.as_dict()
    assert "points" in d
    assert "average_delta" in d
    assert "is_accelerating" in d
    assert "is_decelerating" in d


def test_is_accelerating_false_for_empty():
    assert not MomentumReport().is_accelerating()


def test_is_decelerating_false_for_empty():
    assert not MomentumReport().is_decelerating()
