"""Unit tests for pgdrift.commands.tag_cmd."""

import argparse
import pytest

from pgdrift.commands import tag_cmd
from pgdrift import tags as tag_store


@pytest.fixture
def tag_dir(tmp_path):
    return str(tmp_path)


def _args(**kwargs):
    defaults = {"directory": "."}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_returns_0(tag_dir, capsys):
    args = _args(tag="release", filename="snap.json", directory=tag_dir)
    rc = tag_cmd.cmd_tag_add(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "release" in out
    assert "snap.json" in out


def test_add_persists_tag(tag_dir):
    args = _args(tag="v3", filename="snap_v3.json", directory=tag_dir)
    tag_cmd.cmd_tag_add(args)
    assert tag_store.resolve_tag("v3", directory=tag_dir) == "snap_v3.json"


def test_remove_existing_returns_0(tag_dir, capsys):
    tag_store.add_tag("old", "old.json", directory=tag_dir)
    args = _args(tag="old", directory=tag_dir)
    rc = tag_cmd.cmd_tag_remove(args)
    assert rc == 0


def test_remove_missing_returns_1(tag_dir, capsys):
    args = _args(tag="ghost", directory=tag_dir)
    rc = tag_cmd.cmd_tag_remove(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_list_empty_returns_0(tag_dir, capsys):
    args = _args(directory=tag_dir)
    rc = tag_cmd.cmd_tag_list(args)
    assert rc == 0
    assert "No tags" in capsys.readouterr().out


def test_list_shows_tags(tag_dir, capsys):
    tag_store.add_tag("mysnap", "snap.json", directory=tag_dir)
    args = _args(directory=tag_dir)
    tag_cmd.cmd_tag_list(args)
    out = capsys.readouterr().out
    assert "mysnap" in out
    assert "snap.json" in out


def test_resolve_existing_returns_0(tag_dir, capsys):
    tag_store.add_tag("prod", "prod.json", directory=tag_dir)
    args = _args(tag="prod", directory=tag_dir)
    rc = tag_cmd.cmd_tag_resolve(args)
    assert rc == 0
    assert "prod.json" in capsys.readouterr().out


def test_resolve_missing_returns_1(tag_dir, capsys):
    args = _args(tag="missing", directory=tag_dir)
    rc = tag_cmd.cmd_tag_resolve(args)
    assert rc == 1
