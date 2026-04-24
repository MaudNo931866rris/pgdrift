"""Tests for pgdrift.commands.cohesion_cmd."""
import argparse
from unittest.mock import MagicMock, patch

import pytest

from pgdrift.commands.cohesion_cmd import cmd_cohesion
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.config import Config, DatabaseProfile


def _col(name: str, dtype: str = "integer") -> ColumnInfo:
    return ColumnInfo(name=name, data_type=dtype, is_nullable=False)


def _make_table(name: str, cols) -> TableSchema:
    return TableSchema(schema="public", name=name, columns={c.name: c for c in cols})


def _make_mock_config(profiles=None):
    cfg = MagicMock(spec=Config)
    profiles = profiles or {"prod": DatabaseProfile(host="localhost", port=5432, dbname="db", user="u", password="")}
    cfg.profiles = profiles
    return cfg


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(profile="prod", schema="public", json=False, config="pgdrift.yml")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _patch_cohesion_cmd():
    return patch("pgdrift.commands.cohesion_cmd.load"), \
           patch("pgdrift.commands.cohesion_cmd.get_profile"), \
           patch("pgdrift.commands.cohesion_cmd.psycopg2.connect"), \
           patch("pgdrift.commands.cohesion_cmd.fetch_schema")


def test_missing_config_returns_1():
    with patch("pgdrift.commands.cohesion_cmd.load", side_effect=FileNotFoundError):
        assert cmd_cohesion(_args()) == 1


def test_unknown_profile_returns_1():
    with patch("pgdrift.commands.cohesion_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.cohesion_cmd.get_profile", return_value=None):
        assert cmd_cohesion(_args(profile="ghost")) == 1


def test_no_tables_returns_0(capsys):
    mock_cfg = _make_mock_config()
    mock_profile = MagicMock()
    mock_conn = MagicMock()
    with patch("pgdrift.commands.cohesion_cmd.load", return_value=mock_cfg), \
         patch("pgdrift.commands.cohesion_cmd.get_profile", return_value=mock_profile), \
         patch("pgdrift.commands.cohesion_cmd.psycopg2.connect", return_value=mock_conn), \
         patch("pgdrift.commands.cohesion_cmd.fetch_schema", return_value={}):
        rc = cmd_cohesion(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "No tables" in captured.out


def test_tables_printed(capsys):
    mock_cfg = _make_mock_config()
    mock_profile = MagicMock()
    mock_conn = MagicMock()
    tables = {"public.users": _make_table("users", [_col("id"), _col("name", "text")])}
    with patch("pgdrift.commands.cohesion_cmd.load", return_value=mock_cfg), \
         patch("pgdrift.commands.cohesion_cmd.get_profile", return_value=mock_profile), \
         patch("pgdrift.commands.cohesion_cmd.psycopg2.connect", return_value=mock_conn), \
         patch("pgdrift.commands.cohesion_cmd.fetch_schema", return_value=tables):
        rc = cmd_cohesion(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "public.users" in captured.out


def test_json_flag_outputs_json(capsys):
    import json
    mock_cfg = _make_mock_config()
    mock_profile = MagicMock()
    mock_conn = MagicMock()
    tables = {"public.orders": _make_table("orders", [_col("id")])}
    with patch("pgdrift.commands.cohesion_cmd.load", return_value=mock_cfg), \
         patch("pgdrift.commands.cohesion_cmd.get_profile", return_value=mock_profile), \
         patch("pgdrift.commands.cohesion_cmd.psycopg2.connect", return_value=mock_conn), \
         patch("pgdrift.commands.cohesion_cmd.fetch_schema", return_value=tables):
        rc = cmd_cohesion(_args(json=True))
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "entries" in data
    assert "average_score" in data
