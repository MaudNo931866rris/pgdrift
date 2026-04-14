"""Tests for pgdrift.commands.plugin_cmd."""

import argparse
import types

import pytest

from pgdrift import plugin
from pgdrift.commands.plugin_cmd import (
    cmd_plugin_clear,
    cmd_plugin_list,
    cmd_plugin_load,
    register,
)


@pytest.fixture(autouse=True)
def _reset():
    plugin.clear()
    yield
    plugin.clear()


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"plugin_cmd": None, "hook": None, "group": "pgdrift.plugins"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _dummy():
    pass


def test_list_no_plugins_returns_0(capsys):
    rc = cmd_plugin_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No plugins" in out


def test_list_shows_registered_plugin(capsys):
    plugin.register("formatter", _dummy)
    rc = cmd_plugin_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "formatter" in out
    assert "_dummy" in out


def test_clear_all_returns_0(capsys):
    plugin.register("formatter", _dummy)
    rc = cmd_plugin_clear(_args(hook=None))
    assert rc == 0
    assert plugin.get_plugins("formatter") == []


def test_clear_specific_hook_returns_0(capsys):
    plugin.register("formatter", _dummy)
    plugin.register("linter", _dummy)
    rc = cmd_plugin_clear(_args(hook="formatter"))
    assert rc == 0
    assert plugin.get_plugins("formatter") == []
    assert _dummy in plugin.get_plugins("linter")


def test_load_no_entry_points_returns_0(capsys):
    rc = cmd_plugin_load(_args(group="pgdrift._nonexistent_group_xyz"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No plugins found" in out


def test_register_adds_plugin_subparser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    register(subparsers)
    args = parser.parse_args(["plugin", "list"])
    assert args.plugin_cmd == "list"
