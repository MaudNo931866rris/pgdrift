"""Tests for pgdrift.commands.compare_cmd."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

from pgdrift.commands.compare_cmd import cmd_compare
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.diff import DriftReport


def _make_table(name: str) -> TableSchema:
    return TableSchema(
        schema="public",
        name=name,
        columns=[ColumnInfo(name="id", data_type="integer", is_nullable=False)],
    )


def _args(**kwargs):
    defaults = dict(
        config="pgdrift.yml",
        profile="prod",
        baseline=None,
        snapshot=None,
        schema="public",
        baselines_dir=None,
        no_color=True,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config(profiles=("prod",)):
    cfg = MagicMock()
    from pgdrift.config import DatabaseProfile
    def _get(c, name):
        if name in profiles:
            return DatabaseProfile(name=name, host="localhost", port=5432, dbname="db", user="u", password="p")
        return None
    return cfg, _get


def test_missing_config_returns_1():
    with patch("pgdrift.commands.compare_cmd.load", side_effect=FileNotFoundError):
        assert cmd_compare(_args()) == 1


def test_unknown_profile_returns_1():
    cfg, _get = _make_mock_config()
    with patch("pgdrift.commands.compare_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.compare_cmd.get_profile", return_value=None):
        assert cmd_compare(_args()) == 1


def test_no_baseline_or_snapshot_returns_1():
    cfg, _get = _make_mock_config()
    profile_obj = MagicMock(dsn="postgresql://localhost/db")
    with patch("pgdrift.commands.compare_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.compare_cmd.get_profile", return_value=profile_obj), \
         patch("pgdrift.commands.compare_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.compare_cmd.fetch_schema", return_value={}):
        assert cmd_compare(_args()) == 1


def test_missing_baseline_returns_1():
    cfg, _get = _make_mock_config()
    profile_obj = MagicMock(dsn="postgresql://localhost/db")
    with patch("pgdrift.commands.compare_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.compare_cmd.get_profile", return_value=profile_obj), \
         patch("pgdrift.commands.compare_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.compare_cmd.fetch_schema", return_value={}), \
         patch("pgdrift.commands.compare_cmd.compare_against_baseline", return_value=None):
        assert cmd_compare(_args(baseline="v1")) == 1


def test_no_drift_returns_0():
    cfg, _get = _make_mock_config()
    profile_obj = MagicMock(dsn="postgresql://localhost/db")
    report = DriftReport(source="v1", target="prod", tables=[])
    result = MagicMock(report=report)
    with patch("pgdrift.commands.compare_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.compare_cmd.get_profile", return_value=profile_obj), \
         patch("pgdrift.commands.compare_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.compare_cmd.fetch_schema", return_value={}), \
         patch("pgdrift.commands.compare_cmd.compare_against_baseline", return_value=result), \
         patch("pgdrift.commands.compare_cmd.format_report", return_value=""):
        assert cmd_compare(_args(baseline="v1")) == 0
