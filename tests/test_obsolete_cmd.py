"""Tests for pgdrift.commands.obsolete_cmd."""
import argparse
from unittest.mock import patch, MagicMock

from pgdrift.commands.obsolete_cmd import cmd_obsolete
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.config import Config, DatabaseProfile


def _make_table(name, cols):
    return TableSchema(schema="public", table=name, columns=cols)


def _col(name, dtype="text"):
    return ColumnInfo(name=name, data_type=dtype, is_nullable=True)


def _args(**kw):
    base = dict(source="src", target="tgt", config="pgdrift.yml", json=False)
    base.update(kw)
    return argparse.Namespace(**base)


def _make_mock_config():
    p = DatabaseProfile(host="localhost", port=5432, dbname="db", user="u", password="p")
    return Config(profiles={"src": p, "tgt": p})


def test_missing_config_returns_1():
    with patch("pgdrift.commands.obsolete_cmd.load", side_effect=FileNotFoundError):
        assert cmd_obsolete(_args()) == 1


def test_unknown_source_returns_1():
    with patch("pgdrift.commands.obsolete_cmd.load", return_value=_make_mock_config()):
        assert cmd_obsolete(_args(source="missing")) == 1


def test_unknown_target_returns_1():
    with patch("pgdrift.commands.obsolete_cmd.load", return_value=_make_mock_config()):
        assert cmd_obsolete(_args(target="missing")) == 1


def test_no_obsolete_returns_0(capsys):
    t = _make_table("users", [_col("id", "int")])
    with patch("pgdrift.commands.obsolete_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.obsolete_cmd.psycopg2.connect") as mock_connect, \
         patch("pgdrift.commands.obsolete_cmd.fetch_schema", return_value=[t]):
        mock_connect.return_value.__enter__ = lambda s: MagicMock()
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)
        result = cmd_obsolete(_args())
    assert result == 0


def test_obsolete_found_returns_1(capsys):
    source = _make_table("users", [_col("id"), _col("bio")])
    target = _make_table("users", [_col("id")])
    call_count = 0

    def fake_fetch(conn):
        nonlocal call_count
        call_count += 1
        return [source] if call_count == 1 else [target]

    with patch("pgdrift.commands.obsolete_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.obsolete_cmd.psycopg2.connect") as mock_connect, \
         patch("pgdrift.commands.obsolete_cmd.fetch_schema", side_effect=fake_fetch):
        mock_connect.return_value.__enter__ = lambda s: MagicMock()
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)
        result = cmd_obsolete(_args())
    assert result == 1
