"""Tests for pgdrift.commands.diff_cmd."""

from __future__ import annotations

from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from pgdrift.commands.diff_cmd import cmd_diff
from pgdrift.config import Config, DatabaseProfile
from pgdrift.diff import DriftReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_config() -> Config:
    profiles = {
        "prod": DatabaseProfile(host="prod-host", port=5432, dbname="app", user="u", password="p"),
        "staging": DatabaseProfile(host="stg-host", port=5432, dbname="app", user="u", password="p"),
    }
    return Config(profiles=profiles)


def _args(source: str = "prod", target: str = "staging", no_color: bool = True) -> Namespace:
    return Namespace(source=source, target=target, no_color=no_color)


def _patch_diff_cmd(config=None, schema=None, report=None, formatted=""):
    """Return a context manager that patches the common diff_cmd dependencies."""
    if config is None:
        config = _make_mock_config()
    return (
        patch("pgdrift.commands.diff_cmd.load", return_value=config),
        patch("pgdrift.commands.diff_cmd.psycopg2.connect"),
        patch("pgdrift.commands.diff_cmd.fetch_schema", return_value=schema or []),
        patch("pgdrift.commands.diff_cmd.compute_drift", return_value=report),
        patch("pgdrift.commands.diff_cmd.format_report", return_value=formatted),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_missing_config_returns_1(tmp_path):
    result = cmd_diff(_args(), config_path=str(tmp_path / "missing.yml"))
    assert result == 1


def test_unknown_source_profile_returns_1(tmp_path):
    cfg_file = tmp_path / "pgdrift.yml"
    with patch("pgdrift.commands.diff_cmd.load", return_value=_make_mock_config()):
        result = cmd_diff(_args(source="nonexistent"), config_path=str(cfg_file))
    assert result == 1


def test_unknown_target_profile_returns_1(tmp_path):
    cfg_file = tmp_path / "pgdrift.yml"
    with patch("pgdrift.commands.diff_cmd.load", return_value=_make_mock_config()):
        result = cmd_diff(_args(target="nonexistent"), config_path=str(cfg_file))
    assert result == 1


def test_no_drift_returns_0(tmp_path):
    cfg_file = tmp_path / "pgdrift.yml"
    empty_report = DriftReport(source_env="prod", target_env="staging", table_diffs=[])

    load_patch, connect_patch, fetch_patch, drift_patch, fmt_patch = _patch_diff_cmd(
        report=empty_report, formatted="No drift."
    )
    with load_patch, connect_patch as mock_connect, fetch_patch, drift_patch, fmt_patch:
        mock_connect.return_value.__enter__ = lambda s: MagicMock()
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        result = cmd_diff(_args(), config_path=str(cfg_file))

    assert result == 0


def test_drift_returns_1(tmp_path):
    from pgdrift.diff import TableDiff
    cfg_file = tmp_path / "pgdrift.yml"
    drift_report = DriftReport(
        source_env="prod",
        target_env="staging",
        table_diffs=[TableDiff(table="public.users", status="added", column_diffs=[])],
    )

    load_patch, connect_patch, fetch_patch, drift_patch, fmt_patch = _patch_diff_cmd(
        report=drift_report, formatted="1 table differs."
    )
    with load_patch, connect_patch as mock_connect, fetch_patch, drift_patch, fmt_patch:
        mock_connect.return_value.__enter__ = lambda s: MagicMock()
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)

        result = cmd_diff(_args(), config_path=str(cfg_file))

    assert result == 1
