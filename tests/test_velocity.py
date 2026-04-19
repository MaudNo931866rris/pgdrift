"""Tests for pgdrift.velocity"""
import pytest
from unittest.mock import patch
from pgdrift.velocity import VelocityPoint, VelocityReport, compute_velocity


def _point(captured_at: str, changes: int) -> VelocityPoint:
    return VelocityPoint(captured_at=captured_at, changes=changes)


def test_empty_report_average_is_zero():
    r = VelocityReport(points=[])
    assert r.average_per_day() == 0.0


def test_single_point_average_is_zero():
    r = VelocityReport(points=[_point("2024-01-01T00:00:00", 5)])
    assert r.average_per_day() == 0.0


def test_peak_returns_none_for_empty():
    r = VelocityReport(points=[])
    assert r.peak() is None


def test_peak_returns_max_changes():
    r = VelocityReport(points=[
        _point("2024-01-01T00:00:00", 2),
        _point("2024-01-03T00:00:00", 8),
        _point("2024-01-05T00:00:00", 3),
    ])
    assert r.peak().changes == 8


def test_average_per_day_calculated():
    r = VelocityReport(points=[
        _point("2024-01-01T00:00:00", 10),
        _point("2024-01-06T00:00:00", 0),
    ])
    # 10 changes over 5 days = 2.0/day
    assert r.average_per_day() == 2.0


def test_as_dict_structure():
    r = VelocityReport(points=[_point("2024-01-01T00:00:00", 4)])
    d = r.as_dict()
    assert "average_per_day" in d
    assert "peak" in d
    assert "points" in d


def test_compute_velocity_empty_audit():
    with patch("pgdrift.velocity.load_audit", return_value=[]):
        r = compute_velocity(".pgdrift/snapshots")
    assert r.points == []


def test_compute_velocity_counts_changes():
    records = [
        {"captured_at": "2024-01-01T00:00:00", "added_tables": ["a"], "removed_tables": [], "modified_tables": ["b"]},
        {"captured_at": "2024-01-03T00:00:00", "added_tables": [], "removed_tables": ["c"], "modified_tables": []},
    ]
    with patch("pgdrift.velocity.load_audit", return_value=records):
        r = compute_velocity(".pgdrift/snapshots")
    assert len(r.points) == 2
    assert r.points[0].changes == 2
    assert r.points[1].changes == 1
