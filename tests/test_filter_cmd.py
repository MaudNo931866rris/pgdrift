"""Tests for pgdrift.commands.filter_cmd."""

import argparse
import pytest

from pgdrift import filter as fil
from pgdrift.commands import filter_cmd


@pytest.fixture()
def filter_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return str(tmp_path)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"kind": "schema", "value": "public", "func": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_schema_returns_0(filter_dir):
    args = _args(kind="schema", value="public", func=filter_cmd.cmd_filter_add)
    assert filter_cmd.cmd_filter_add(args) == 0


def test_add_table_returns_0(filter_dir):
    args = _args(kind="table", value="public.tmp_*", func=filter_cmd.cmd_filter_add)
    assert filter_cmd.cmd_filter_add(args) == 0


def test_add_persists_schema(filter_dir):
    args = _args(kind="schema", value="reporting")
    filter_cmd.cmd_filter_add(args)
    result = fil.load_filters()
    assert "reporting" in result["schemas"]


def test_remove_existing_returns_0(filter_dir):
    fil.add_schema_filter("public")
    args = _args(kind="schema", value="public", func=filter_cmd.cmd_filter_remove)
    assert filter_cmd.cmd_filter_remove(args) == 0


def test_remove_missing_returns_1(filter_dir):
    args = _args(kind="schema", value="ghost", func=filter_cmd.cmd_filter_remove)
    assert filter_cmd.cmd_filter_remove(args) == 1


def test_list_no_filters_returns_0(filter_dir, capsys):
    args = _args(func=filter_cmd.cmd_filter_list)
    assert filter_cmd.cmd_filter_list(args) == 0
    out = capsys.readouterr().out
    assert "No filters" in out


def test_list_shows_schema(filter_dir, capsys):
    fil.add_schema_filter("public")
    args = _args(func=filter_cmd.cmd_filter_list)
    filter_cmd.cmd_filter_list(args)
    out = capsys.readouterr().out
    assert "public" in out
