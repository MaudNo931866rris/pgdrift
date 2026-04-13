"""Tests for pgdrift.baseline and pgdrift.commands.baseline_cmd."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

import pgdrift.baseline as bl
from pgdrift.commands.baseline_cmd import (
    cmd_baseline_save,
    cmd_baseline_list,
    cmd_baseline_show,
    cmd_baseline_delete,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(tmp_path: Path, **kwargs) -> argparse.Namespace:
    defaults = {
        "baseline_dir": str(tmp_path),
        "name": "v1",
        "tables": "",
        "note": "",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# pgdrift.baseline unit tests
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    path = bl.save_baseline("release-1", ["users", "orders"], base_dir=tmp_path)
    assert path.exists()


def test_save_file_contains_expected_keys(tmp_path):
    bl.save_baseline("release-1", ["users"], note="initial", base_dir=tmp_path)
    data = json.loads((tmp_path / "release-1.json").read_text())
    assert data["name"] == "release-1"
    assert "created_at" in data
    assert data["note"] == "initial"
    assert "users" in data["acknowledged_tables"]


def test_load_returns_none_for_missing(tmp_path):
    assert bl.load_baseline("nonexistent", base_dir=tmp_path) is None


def test_roundtrip(tmp_path):
    tables = ["accounts", "sessions"]
    bl.save_baseline("snap", tables, base_dir=tmp_path)
    data = bl.load_baseline("snap", base_dir=tmp_path)
    assert data is not None
    assert data["acknowledged_tables"] == sorted(tables)


def test_list_baselines(tmp_path):
    bl.save_baseline("alpha", ["t1"], base_dir=tmp_path)
    bl.save_baseline("beta", ["t2"], base_dir=tmp_path)
    assert bl.list_baselines(base_dir=tmp_path) == ["alpha", "beta"]


def test_delete_removes_file(tmp_path):
    bl.save_baseline("to-delete", ["t"], base_dir=tmp_path)
    assert bl.delete_baseline("to-delete", base_dir=tmp_path) is True
    assert bl.load_baseline("to-delete", base_dir=tmp_path) is None


def test_delete_returns_false_if_not_found(tmp_path):
    assert bl.delete_baseline("ghost", base_dir=tmp_path) is False


# ---------------------------------------------------------------------------
# baseline_cmd tests
# ---------------------------------------------------------------------------

def test_cmd_save_returns_0(tmp_path):
    args = _args(tmp_path, tables="users,orders")
    assert cmd_baseline_save(args) == 0


def test_cmd_save_no_tables_returns_1(tmp_path):
    args = _args(tmp_path, tables="")
    # patch stdin to be empty
    import io, sys
    old = sys.stdin
    sys.stdin = io.StringIO("")
    try:
        assert cmd_baseline_save(args) == 1
    finally:
        sys.stdin = old


def test_cmd_list_empty(tmp_path, capsys):
    args = _args(tmp_path)
    assert cmd_baseline_list(args) == 0
    assert "No baselines" in capsys.readouterr().out


def test_cmd_show_missing_returns_1(tmp_path):
    args = _args(tmp_path, name="missing")
    assert cmd_baseline_show(args) == 1


def test_cmd_show_existing_prints_json(tmp_path, capsys):
    bl.save_baseline("v1", ["t"], base_dir=tmp_path)
    args = _args(tmp_path, name="v1")
    assert cmd_baseline_show(args) == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["name"] == "v1"


def test_cmd_delete_missing_returns_1(tmp_path):
    args = _args(tmp_path, name="ghost")
    assert cmd_baseline_delete(args) == 1


def test_cmd_delete_existing_returns_0(tmp_path):
    bl.save_baseline("v1", ["t"], base_dir=tmp_path)
    args = _args(tmp_path, name="v1")
    assert cmd_baseline_delete(args) == 0
