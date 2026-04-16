"""Tests for pgdrift.pin and pgdrift.commands.pin_cmd."""
from __future__ import annotations

import json
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.pin import save_pin, load_pin, load_pin_tables, delete_pin, list_pins
from pgdrift.commands.pin_cmd import cmd_pin_save, cmd_pin_show, cmd_pin_delete, cmd_pin_list


def _make_table(name="users", schema="public"):
    col = ColumnInfo(name="id", data_type="integer", is_nullable=False)
    return TableSchema(name=name, schema=schema, columns=[col])


@pytest.fixture
def pin_dir(tmp_path):
    return str(tmp_path / "pins")


def test_save_creates_file(pin_dir):
    tables = [_make_table()]
    path = save_pin("prod", tables, pin_dir=pin_dir)
    assert path.exists()


def test_save_file_contains_profile(pin_dir):
    save_pin("prod", [_make_table()], pin_dir=pin_dir)
    data = load_pin("prod", pin_dir=pin_dir)
    assert data["profile"] == "prod"


def test_roundtrip_preserves_tables(pin_dir):
    tables = [_make_table("orders"), _make_table("users")]
    save_pin("staging", tables, pin_dir=pin_dir)
    loaded = load_pin_tables("staging", pin_dir=pin_dir)
    assert len(loaded) == 2
    assert {t.name for t in loaded} == {"orders", "users"}


def test_load_returns_none_for_missing(pin_dir):
    assert load_pin("ghost", pin_dir=pin_dir) is None

_removes_file(pin_dir):
    save_pin("dev", [_make_table()], pin_dir=pin_dir)
    assert delete_pin("dev", pin_dir=pin_dir) is True
    assert load_pin("dev", pin_dir=pin_dir) is None


def test_delete_missing_returns_false(pin_dir):
    assert delete_pin("nobody", pin_dir=pin_dir) is False


def test_list_pins(pin_dir):
    save_pin("a", [_make_table()], pin_dir=pin_dir)
    save_pin("b", [_make_table()], pin_dir=pin_dir)
    assert set(list_pins(pin_dir=pin_dir)) == {"a", "b"}


def _args(**kw):
    ns = types.SimpleNamespace(config="pgdrift.yml", **kw)
    return ns


def _make_mock_config(profile_name="prod"):
    profile = MagicMock()
    profile.dsn = "postgresql://localhost/test"
    cfg = MagicMock()
    cfg.get_profile = lambda n: profile if n == profile_name else None
    return cfg


def test_cmd_pin_save_missing_config():
    with patch("pgdrift.commands.pin_cmd.load", side_effect=FileNotFoundError):
        assert cmd_pin_save(_args(profile="prod")) == 1


def test_cmd_pin_save_unknown_profile():
    with patch("pgdrift.commands.pin_cmd.load", return_value=_make_mock_config()):
        assert cmd_pin_save(_args(profile="unknown")) == 1


def test_cmd_pin_show_missing_returns_1(capsys):
    with patch("pgdrift.commands.pin_cmd.load_pin", return_value=None):
        assert cmd_pin_show(_args(profile="ghost")) == 1


def test_cmd_pin_delete_missing_returns_1():
    with patch("pgdrift.commands.pin_cmd.delete_pin", return_value=False):
        assert cmd_pin_delete(_args(profile="ghost")) == 1


def test_cmd_pin_list_empty(capsys):
    with patch("pgdrift.commands.pin_cmd.list_pins", return_value=[]):
        assert cmd_pin_list(_args()) == 0
    out = capsys.readouterr().out
    assert "No pins" in out
