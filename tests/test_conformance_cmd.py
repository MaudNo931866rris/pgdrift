"""Tests for pgdrift.commands.conformance_cmd."""
import argparse
import pytest
from unittest.mock import patch, MagicMock

from pgdrift.commands.conformance_cmd import cmd_conformance
from pgdrift.config import Config, DatabaseProfile
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.conformance import ConformanceReport


def _col(name, dtype="integer", nullable=False):
    return ColumnInfo(name=name, data_type=dtype, nullable=nullable)


def _make_table(name, cols=None):
    return TableSchema(
        schema="public",
        name=name,
        columns=cols or [_col("id")],
    )


def _make_mock_config(profiles=None):
    cfg = MagicMock(spec=Config)
    profiles = profiles or {"prod": DatabaseProfile(host="localhost", port=5432, dbname="db", user="u", password="")}
    cfg.profiles = profiles
    return cfg


def _args(**kwargs):
    defaults = dict(config="pgdrift.yml", profile="prod", schema="public", json=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@patch("pgdrift.commands.conformance_cmd.load", side_effect=FileNotFoundError)
def test_missing_config_returns_1(mock_load):
    assert cmd_conformance(_args()) == 1


@patch("pgdrift.commands.conformance_cmd.load")
@patch("pgdrift.commands.conformance_cmd.get_profile", return_value=None)
def test_unknown_profile_returns_1(mock_gp, mock_load):
    assert cmd_conformance(_args(profile="ghost")) == 1


@patch("pgdrift.commands.conformance_cmd.psycopg2.connect")
@patch("pgdrift.commands.conformance_cmd.fetch_schema")
@patch("pgdrift.commands.conformance_cmd.compute_conformance")
@patch("pgdrift.commands.conformance_cmd.get_profile")
@patch("pgdrift.commands.conformance_cmd.load")
def test_no_violations_returns_0(mock_load, mock_gp, mock_cc, mock_fs, mock_conn):
    mock_gp.return_value = MagicMock(dsn="postgresql://localhost/db")
    mock_fs.return_value = [_make_table("users")]
    mock_cc.return_value = ConformanceReport(violations=[])
    assert cmd_conformance(_args()) == 0


@patch("pgdrift.commands.conformance_cmd.psycopg2.connect")
@patch("pgdrift.commands.conformance_cmd.fetch_schema")
@patch("pgdrift.commands.conformance_cmd.compute_conformance")
@patch("pgdrift.commands.conformance_cmd.get_profile")
@patch("pgdrift.commands.conformance_cmd.load")
def test_violations_returns_1(mock_load, mock_gp, mock_cc, mock_fs, mock_conn):
    from pgdrift.conformance import ConformanceViolation
    mock_gp.return_value = MagicMock(dsn="postgresql://localhost/db")
    mock_fs.return_value = [_make_table("BadTable")]
    mock_cc.return_value = ConformanceReport(
        violations=[ConformanceViolation("BadTable", "", "snake_case_table", "bad")]
    )
    assert cmd_conformance(_args()) == 1


@patch("pgdrift.commands.conformance_cmd.psycopg2.connect")
@patch("pgdrift.commands.conformance_cmd.fetch_schema")
@patch("pgdrift.commands.conformance_cmd.compute_conformance")
@patch("pgdrift.commands.conformance_cmd.get_profile")
@patch("pgdrift.commands.conformance_cmd.load")
def test_json_flag_outputs_json(mock_load, mock_gp, mock_cc, mock_fs, mock_conn, capsys):
    mock_gp.return_value = MagicMock(dsn="postgresql://localhost/db")
    mock_fs.return_value = []
    mock_cc.return_value = ConformanceReport(violations=[])
    ret = cmd_conformance(_args(json=True))
    captured = capsys.readouterr()
    assert ret == 0
    import json
    data = json.loads(captured.out)
    assert "violations" in data
