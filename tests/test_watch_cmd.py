"""Tests for pgdrift.commands.watch_cmd."""

from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from pgdrift.commands.watch_cmd import cmd_watch
from pgdrift.config import Config, DatabaseProfile
from pgdrift.diff import DriftReport


def _make_mock_config():
    profile = DatabaseProfile(
        host="localhost", port=5432, dbname="test", user="u", password="p"
    )
    return Config(profiles={"src": profile, "tgt": profile})


def _args(**kwargs):
    defaults = {
        "config": "pgdrift.yml",
        "source": "src",
        "target": "tgt",
        "interval": 1,
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_missing_config_returns_1():
    with patch("pgdrift.commands.watch_cmd.load", side_effect=FileNotFoundError):
        result = cmd_watch(_args())
    assert result == 1


def test_unknown_source_profile_returns_1():
    with patch("pgdrift.commands.watch_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.watch_cmd.get_profile", side_effect=KeyError):
        result = cmd_watch(_args())
    assert result == 1


def test_unknown_target_profile_returns_1():
    cfg = _make_mock_config()
    profile = cfg.profiles["src"]

    def _get_profile(config, name):
        if name == "tgt":
            raise KeyError(name)
        return profile

    with patch("pgdrift.commands.watch_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.watch_cmd.get_profile", side_effect=_get_profile):
        result = cmd_watch(_args())
    assert result == 1


def test_watch_stops_on_keyboard_interrupt(capsys):
    """KeyboardInterrupt during sleep should exit with 0."""
    no_drift = DriftReport(source="src", target="tgt", tables=[])

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("pgdrift.commands.watch_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.watch_cmd.get_profile", return_value=_make_mock_config().profiles["src"]), \
         patch("pgdrift.commands.watch_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.watch_cmd.compute_drift", return_value=no_drift), \
         patch("pgdrift.commands.watch_cmd.format_report", return_value=""), \
         patch("psycopg2.connect", return_value=mock_conn), \
         patch("time.sleep", side_effect=KeyboardInterrupt):
        result = cmd_watch(_args())

    assert result == 0
    captured = capsys.readouterr()
    assert "Watch stopped" in captured.out


def test_watch_prints_drift_when_detected(capsys):
    from pgdrift.diff import TableDiff

    drift_report = DriftReport(
        source="src",
        target="tgt",
        tables=[TableDiff(table="public.users", added_columns=[], removed_columns=[], changed_columns=[])],
    )
    drift_report.has_drift = True  # type: ignore[attr-defined]

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("pgdrift.commands.watch_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.watch_cmd.get_profile", return_value=_make_mock_config().profiles["src"]), \
         patch("pgdrift.commands.watch_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.watch_cmd.compute_drift", return_value=drift_report), \
         patch("pgdrift.commands.watch_cmd.format_report", return_value="diff output"), \
         patch("psycopg2.connect", return_value=mock_conn), \
         patch("time.sleep", side_effect=KeyboardInterrupt):
        result = cmd_watch(_args())

    assert result == 0
    captured = capsys.readouterr()
    assert "DRIFT DETECTED" in captured.out
