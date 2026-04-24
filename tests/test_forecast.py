"""Tests for pgdrift.forecast"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from pgdrift.forecast import (
    ForecastPoint,
    ForecastReport,
    _moving_average,
    _std_dev,
    build_forecast,
)
from pgdrift.trend import TrendPoint


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_moving_average_empty_returns_zero():
    assert _moving_average([], 3) == 0.0


def test_moving_average_uses_last_n():
    assert _moving_average([1.0, 2.0, 9.0], 2) == pytest.approx(5.5)


def test_std_dev_single_value_is_zero():
    assert _std_dev([42.0]) == 0.0


def test_std_dev_uniform_values_is_zero():
    assert _std_dev([3.0, 3.0, 3.0]) == pytest.approx(0.0)


def test_std_dev_known_values():
    result = _std_dev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert result == pytest.approx(2.0, rel=1e-3)


# ---------------------------------------------------------------------------
# ForecastReport
# ---------------------------------------------------------------------------

def test_forecast_report_is_empty_when_no_forecast():
    r = ForecastReport(profile="prod")
    assert r.is_empty()


def test_forecast_report_not_empty_with_points():
    fp = ForecastPoint(period="week+1", predicted_changes=3.0, lower_bound=1.0, upper_bound=5.0)
    r = ForecastReport(profile="prod", forecast=[fp])
    assert not r.is_empty()


def test_forecast_point_as_dict_keys():
    fp = ForecastPoint(period="week+1", predicted_changes=3.14159, lower_bound=1.0, upper_bound=5.0)
    d = fp.as_dict()
    assert set(d.keys()) == {"period", "predicted_changes", "lower_bound", "upper_bound"}
    assert d["predicted_changes"] == pytest.approx(3.14, rel=1e-2)


# ---------------------------------------------------------------------------
# build_forecast integration
# ---------------------------------------------------------------------------

def _make_audit_entry(total: int) -> dict:
    from pgdrift.diff import DriftReport
    return {
        "captured_at": "2024-01-01T00:00:00",
        "report": DriftReport(
            source="prod", target="staging",
            added_tables=[], removed_tables=[],
            modified_tables=[],
        ),
    }


def test_build_forecast_no_audit_returns_empty():
    with patch("pgdrift.forecast.load_audit", return_value=[]):
        r = build_forecast(profile="prod")
    assert r.is_empty()


def test_build_forecast_returns_correct_horizon_count():
    from pgdrift.diff import DriftReport
    fake_records = [
        {"captured_at": "2024-01-01T00:00:00", "report": DriftReport(
            source="prod", target="staging",
            added_tables=[], removed_tables=[], modified_tables=[]
        )}
        for _ in range(5)
    ]
    with patch("pgdrift.forecast.load_audit", return_value=fake_records):
        r = build_forecast(profile="prod", horizons=6)
    assert len(r.forecast) == 6


def test_build_forecast_lower_bound_non_negative():
    from pgdrift.diff import DriftReport
    fake_records = [
        {"captured_at": "2024-01-01T00:00:00", "report": DriftReport(
            source="prod", target="staging",
            added_tables=[], removed_tables=[], modified_tables=[]
        )}
    ]
    with patch("pgdrift.forecast.load_audit", return_value=fake_records):
        r = build_forecast(profile="prod")
    for fp in r.forecast:
        assert fp.lower_bound >= 0.0
