"""Tests for pgdrift.commands.forecast_cmd"""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

from pgdrift.commands.forecast_cmd import cmd_forecast
from pgdrift.forecast import ForecastPoint, ForecastReport
from pgdrift.trend import TrendPoint


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "config": "pgdrift.yml",
        "profile": "prod",
        "snapshot_dir": "snapshots",
        "horizons": 4,
        "window": 3,
        "json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config(profiles=("prod",)):
    cfg = MagicMock()
    def _get(name):
        if name not in profiles:
            raise KeyError(name)
        return MagicMock()
    cfg.get_profile.side_effect = _get
    return cfg


def test_missing_config_returns_1(tmp_path):
    args = _args(config=str(tmp_path / "missing.yml"))
    assert cmd_forecast(args) == 1


def test_unknown_profile_returns_1():
    args = _args(profile="unknown")
    cfg = _make_mock_config(profiles=("prod",))
    with patch("pgdrift.commands.forecast_cmd.load", return_value=cfg):
        result = cmd_forecast(args)
    assert result == 1


def test_no_history_returns_0(capsys):
    args = _args()
    cfg = _make_mock_config()
    empty_report = ForecastReport(profile="prod", history=[], forecast=[])
    with patch("pgdrift.commands.forecast_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.forecast_cmd.build_forecast", return_value=empty_report):
        result = cmd_forecast(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "No historical data" in out


def test_forecast_table_printed(capsys):
    args = _args()
    cfg = _make_mock_config()
    fp = ForecastPoint(period="week+1", predicted_changes=5.0, lower_bound=3.0, upper_bound=7.0)
    report = ForecastReport(
        profile="prod",
        history=[TrendPoint(label="2024-01-01", total_changes=5)],
        forecast=[fp],
    )
    with patch("pgdrift.commands.forecast_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.forecast_cmd.build_forecast", return_value=report):
        result = cmd_forecast(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "week+1" in out
    assert "5.00" in out


def test_json_flag_outputs_valid_json(capsys):
    import json
    args = _args(json=True)
    cfg = _make_mock_config()
    fp = ForecastPoint(period="week+1", predicted_changes=2.0, lower_bound=1.0, upper_bound=3.0)
    report = ForecastReport(
        profile="prod",
        history=[TrendPoint(label="2024-01-01", total_changes=2)],
        forecast=[fp],
    )
    with patch("pgdrift.commands.forecast_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.forecast_cmd.build_forecast", return_value=report):
        result = cmd_forecast(args)
    assert result == 0
    data = json.loads(capsys.readouterr().out)
    assert data["profile"] == "prod"
    assert len(data["forecast"]) == 1
