"""Tests for pgdrift.commands.snapshot_cmd."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pgdrift.commands.snapshot_cmd import cmd_capture, cmd_compare_snapshot


def _args(**kwargs):
    defaults = {
        "config": "pgdrift.yml",
        "profile": "staging",
        "output": "",
        "snapshot": "",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@patch("pgdrift.commands.snapshot_cmd.load", side_effect=FileNotFoundError("not found"))
def test_capture_missing_config_returns_1(mock_load, tmp_path):
    rc = cmd_capture(_args(output=str(tmp_path / "snap.json")))
    assert rc == 1


@patch("pgdrift.commands.snapshot_cmd.load")
@patch("pgdrift.commands.snapshot_cmd.get_profile", side_effect=KeyError("staging"))
def test_capture_unknown_profile_returns_1(mock_gp, mock_load, tmp_path):
    rc = cmd_capture(_args(output=str(tmp_path / "snap.json")))
    assert rc == 1


@patch("pgdrift.commands.snapshot_cmd.psycopg2.connect")
@patch("pgdrift.commands.snapshot_cmd.fetch_schema", return_value={})
@patch("pgdrift.commands.snapshot_cmd.get_profile")
@patch("pgdrift.commands.snapshot_cmd.load")
def test_capture_saves_file(mock_load, mock_gp, mock_fetch, mock_connect, tmp_path):
    out = tmp_path / "snap.json"
    mock_connect.return_value.__enter__ = lambda s: s
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value.close = MagicMock()
    rc = cmd_capture(_args(output=str(out)))
    assert rc == 0
    assert out.exists()


@patch("pgdrift.commands.snapshot_cmd.load", side_effect=FileNotFoundError("not found"))
def test_compare_snapshot_missing_config_returns_1(mock_load, tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text("{}")
    rc = cmd_compare_snapshot(_args(snapshot=str(snap)))
    assert rc == 1


@patch("pgdrift.commands.snapshot_cmd.load")
@patch("pgdrift.commands.snapshot_cmd.get_profile")
def test_compare_snapshot_missing_file_returns_1(mock_gp, mock_load, tmp_path):
    rc = cmd_compare_snapshot(_args(snapshot=str(tmp_path / "missing.json")))
    assert rc == 1
