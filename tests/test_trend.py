"""Tests for pgdrift.trend."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from pgdrift.trend import TrendPoint, TrendReport, _point_from_report, build_trend
from pgdrift.diff import DriftReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_drift_report(added=0, removed=0, modified=0) -> DriftReport:
    return DriftReport(
        source_name="prod",
        target_name="prod",
        added_tables=[f"public.t{i}" for i in range(added)],
        removed_tables=[f"public.d{i}" for i in range(removed)],
        modified_tables=[object() for _ in range(modified)],  # type: ignore[list-item]
    )


# ---------------------------------------------------------------------------
# TrendPoint / TrendReport unit tests
# ---------------------------------------------------------------------------

def test_point_from_report_counts_correctly():
    report = _make_drift_report(added=2, removed=1, modified=3)
    point = _point_from_report(report, "2024-01-01T00:00:00", "prod")
    assert point.added_tables == 2
    assert point.removed_tables == 1
    assert point.modified_tables == 3
    assert point.total_changes == 6


def test_trend_report_is_stable_when_no_changes():
    report = TrendReport(profile="prod", points=[
        TrendPoint("2024-01-01", "prod", 0, 0, 0, 0),
        TrendPoint("2024-01-02", "prod", 0, 0, 0, 0),
    ])
    assert report.is_stable() is True


def test_trend_report_not_stable_when_changes_exist():
    report = TrendReport(profile="prod", points=[
        TrendPoint("2024-01-01", "prod", 0, 0, 0, 0),
        TrendPoint("2024-01-02", "prod", 1, 0, 0, 1),
    ])
    assert report.is_stable() is False


def test_peak_returns_none_for_empty_report():
    report = TrendReport(profile="prod", points=[])
    assert report.peak() is None


def test_peak_returns_highest_change_point():
    p1 = TrendPoint("2024-01-01", "prod", 1, 0, 0, 1)
    p2 = TrendPoint("2024-01-02", "prod", 3, 1, 2, 6)
    p3 = TrendPoint("2024-01-03", "prod", 0, 0, 1, 1)
    report = TrendReport(profile="prod", points=[p1, p2, p3])
    assert report.peak() is p2


# ---------------------------------------------------------------------------
# build_trend integration (mocked history)
# ---------------------------------------------------------------------------

_ENTRY_1 = {"file": "snap1.json", "captured_at": "2024-01-01T00:00:00"}
_ENTRY_2 = {"file": "snap2.json", "captured_at": "2024-01-02T00:00:00"}

_SNAP_1 = {"tables": {"public.users": {"columns": []}}}
_SNAP_2 = {"tables": {
    "public.users": {"columns": []},
    "public.orders": {"columns": []},
}}


def test_build_trend_returns_empty_for_single_snapshot():
    with patch("pgdrift.trend.list_history", return_value=[_ENTRY_1]), \
         patch("pgdrift.trend.load_history", return_value=_SNAP_1):
        trend = build_trend("prod")
    assert trend.profile == "prod"
    assert trend.points == []


def test_build_trend_detects_added_table():
    snapshots = {"snap1.json": _SNAP_1, "snap2.json": _SNAP_2}

    with patch("pgdrift.trend.list_history", return_value=[_ENTRY_1, _ENTRY_2]), \
         patch("pgdrift.trend.load_history", side_effect=lambda f: snapshots[f]), \
         patch("pgdrift.trend.compute_drift") as mock_drift:
        mock_drift.return_value = _make_drift_report(added=1)
        trend = build_trend("prod")

    assert len(trend.points) == 1
    assert trend.points[0].added_tables == 1
    assert trend.is_stable() is False
