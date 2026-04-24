"""Tests for pgdrift.resolution."""

import json
import pytest
from pathlib import Path

from pgdrift.resolution import (
    ResolutionEntry,
    ResolutionReport,
    add_resolution,
    load_resolutions,
    remove_resolution,
    save_resolutions,
    _resolution_path,
)


@pytest.fixture()
def res_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_load_returns_empty_when_no_file(res_dir):
    report = load_resolutions("prod")
    assert report.entries == []


def test_add_creates_entry(res_dir):
    entry = add_resolution("prod", "users", reason="acknowledged by team")
    assert entry.table == "users"
    assert entry.column is None
    assert entry.reason == "acknowledged by team"


def test_add_persists_to_disk(res_dir):
    add_resolution("prod", "orders", reason="planned migration")
    path = _resolution_path("prod")
    assert path.exists()
    data = json.loads(path.read_text())
    assert any(r["table"] == "orders" for r in data["entries"])


def test_add_column_resolution(res_dir):
    entry = add_resolution("prod", "users", reason="deprecated", column="old_col")
    assert entry.key() == "users.old_col"


def test_add_overwrites_existing_key(res_dir):
    add_resolution("prod", "users", reason="first")
    add_resolution("prod", "users", reason="updated")
    report = load_resolutions("prod")
    matching = [e for e in report.entries if e.table == "users"]
    assert len(matching) == 1
    assert matching[0].reason == "updated"


def test_remove_existing_returns_true(res_dir):
    add_resolution("prod", "users", reason="test")
    result = remove_resolution("prod", "users")
    assert result is True


def test_remove_missing_returns_false(res_dir):
    result = remove_resolution("prod", "nonexistent")
    assert result is False


def test_remove_deletes_entry(res_dir):
    add_resolution("prod", "users", reason="test")
    remove_resolution("prod", "users")
    report = load_resolutions("prod")
    assert not any(e.table == "users" for e in report.entries)


def test_is_resolved_table(res_dir):
    add_resolution("prod", "users", reason="ok")
    report = load_resolutions("prod")
    assert report.is_resolved("users") is True
    assert report.is_resolved("orders") is False


def test_is_resolved_column(res_dir):
    add_resolution("prod", "users", reason="ok", column="email")
    report = load_resolutions("prod")
    assert report.is_resolved("users", "email") is True
    assert report.is_resolved("users", "name") is False


def test_by_table_filters_correctly(res_dir):
    add_resolution("prod", "users", reason="a", column="col1")
    add_resolution("prod", "users", reason="b", column="col2")
    add_resolution("prod", "orders", reason="c")
    report = load_resolutions("prod")
    assert len(report.by_table("users")) == 2
    assert len(report.by_table("orders")) == 1
