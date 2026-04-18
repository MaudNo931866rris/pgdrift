import argparse
import pytest
from unittest.mock import patch, MagicMock
from pgdrift.commands.complexity_cmd import cmd_complexity
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.config import Config, DatabaseProfile


def _col(name, dtype, nullable=False):
    return ColumnInfo(name=name, data_type=dtype, nullable=nullable, default=None)


def _make_mock_config(profiles=None):
    cfg = MagicMock(spec=Config)
    profiles = profiles or {"prod": DatabaseProfile(host="h", port=5432, user="u", password="p", dbname="d")}
    cfg.profiles = profiles
    return cfg


def _args(**kwargs):
    defaults = {"profile": "prod", "config": "pgdrift.yml", "json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_missing_config_returns_1():
    with patch("pgdrift.commands.complexity_cmd.load", side_effect=FileNotFoundError):
        assert cmd_complexity(_args()) == 1


def test_unknown_profile_returns_1():
    cfg = _make_mock_config()
    with patch("pgdrift.commands.complexity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.complexity_cmd.get_profile", return_value=None):
        assert cmd_complexity(_args(profile="ghost")) == 1


def test_complexity_returns_0(capsys):
    cfg = _make_mock_config()
    profile = cfg.profiles["prod"]
    tables = [
        TableSchema(schema="public", name="users", columns=[
            _col("id", "integer"),
            _col("email", "text", True),
        ])
    ]
    with patch("pgdrift.commands.complexity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.complexity_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.complexity_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.complexity_cmd.fetch_schema", return_value=tables):
        result = cmd_complexity(_args())
    assert result == 0
    out = capsys.readouterr().out
    assert "users" in out


def test_complexity_json_output(capsys):
    import json
    cfg = _make_mock_config()
    profile = cfg.profiles["prod"]
    tables = [
        TableSchema(schema="public", name="orders", columns=[_col("id", "integer")])
    ]
    with patch("pgdrift.commands.complexity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.complexity_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.complexity_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.complexity_cmd.fetch_schema", return_value=tables):
        result = cmd_complexity(_args(json=True))
    assert result == 0
    data = json.loads(capsys.readouterr().out)
    assert "tables" in data
    assert data["tables"][0]["table"] == "public.orders"
