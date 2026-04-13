"""Tests for pgdrift.cli."""

import pytest
from unittest.mock import patch, MagicMock

from pgdrift.cli import run
from pgdrift.diff import DriftReport


MOCK_CONFIG_PATH = "pgdrift.yml"


def _make_mock_config():
    from pgdrift.config import Config, DatabaseProfile
    profile = DatabaseProfile(host="localhost", port=5432, dbname="mydb", user="u", password="p")
    return Config(profiles={"dev": profile, "prod": profile})


@patch("pgdrift.cli.load")
def test_missing_config_returns_1(mock_load):
    mock_load.side_effect = FileNotFoundError("not found")
    result = run(["dev", "prod", "--config", "missing.yml"])
    assert result == 1


@patch("pgdrift.cli.psycopg2.connect")
@patch("pgdrift.cli.fetch_schema")
@patch("pgdrift.cli.build_report")
@patch("pgdrift.cli.load")
def test_no_drift_returns_0(mock_load, mock_build, mock_fetch, mock_connect):
    mock_load.return_value = _make_mock_config()
    mock_fetch.return_value = {}
    mock_build.return_value = DriftReport(source_env="dev", target_env="prod", table_diffs=[])
    mock_connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    result = run(["dev", "prod"])
    assert result == 0


@patch("pgdrift.cli.psycopg2.connect")
@patch("pgdrift.cli.fetch_schema")
@patch("pgdrift.cli.build_report")
@patch("pgdrift.cli.load")
def test_drift_returns_1(mock_load, mock_build, mock_fetch, mock_connect):
    from pgdrift.diff import TableDiff
    mock_load.return_value = _make_mock_config()
    mock_fetch.return_value = {}
    mock_build.return_value = DriftReport(
        source_env="dev",
        target_env="prod",
        table_diffs=[TableDiff(table_name="t", status="added", column_diffs=[])],
    )
    mock_connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    result = run(["dev", "prod"])
    assert result == 1


@patch("pgdrift.cli.load")
def test_unknown_profile_returns_1(mock_load):
    mock_load.return_value = _make_mock_config()
    result = run(["dev", "unknown_env"])
    assert result == 1
