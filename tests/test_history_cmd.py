"""Tests for pgdrift.commands.history_cmd."""

from __future__ import annotations

import argparse
import json
import os

import pytest

from pgdrift.commands.history_cmd import (
    cmd_history_list,
    cmd_history_show,
    cmd_history_clear,
    HISTORY_DIR,
)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"history_dir": HISTORY_DIR, "history_action": "list"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_list_no_snapshots(tmp_path, capsys):
    rc = cmd_history_list(_args(history_dir=str(tmp_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_list_shows_files(tmp_path, capsys):
    (tmp_path / "prod_20240101T000000Z.json").write_text(json.dumps({"tables": []}))
    rc = cmd_history_list(_args(history_dir=str(tmp_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "prod_20240101T000000Z.json" in out


def test_show_missing_returns_1(tmp_path, capsys):
    rc = cmd_history_show(_args(history_dir=str(tmp_path), name="nonexistent"))
    assert rc == 1


def test_show_existing_prints_json(tmp_path, capsys):
    data = {"profile": "prod", "tables": []}
    (tmp_path / "snap.json").write_text(json.dumps(data))
    rc = cmd_history_show(_args(history_dir=str(tmp_path), name="snap"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "prod" in out


def test_clear_removes_files(tmp_path, capsys):
    for i in range(3):
        (tmp_path / f"snap_{i}.json").write_text("{}")
    rc = cmd_history_clear(_args(history_dir=str(tmp_path)))
    assert rc == 0
    assert list_json(tmp_path) == []


def test_clear_empty_dir(tmp_path, capsys):
    rc = cmd_history_clear(_args(history_dir=str(tmp_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Nothing" in out


def list_json(path):
    return [f for f in os.listdir(path) if f.endswith(".json")]
