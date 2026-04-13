"""Tests for pgdrift.history module."""

from __future__ import annotations

import json
import os

import pytest

from pgdrift.history import save_history, load_history, list_history
from pgdrift.inspector import ColumnInfo, TableSchema


def _make_table(name: str = "users", schema: str = "public") -> TableSchema:
    col = ColumnInfo(name="id", data_type="integer", is_nullable=False)
    return TableSchema(schema=schema, name=name, columns=[col])


def test_save_creates_file(tmp_path):
    tables = [_make_table()]
    path = save_history(tables, "prod", directory=str(tmp_path), timestamp="20240101T000000Z")
    assert os.path.exists(path)


def test_save_file_contains_profile(tmp_path):
    tables = [_make_table()]
    path = save_history(tables, "staging", directory=str(tmp_path), timestamp="20240101T000000Z")
    with open(path) as fh:
        data = json.load(fh)
    assert data["profile"] == "staging"


def test_save_file_contains_captured_at(tmp_path):
    tables = [_make_table()]
    ts = "20240601T120000Z"
    path = save_history(tables, "dev", directory=str(tmp_path), timestamp=ts)
    with open(path) as fh:
        data = json.load(fh)
    assert data["captured_at"] == ts


def test_roundtrip_preserves_tables(tmp_path):
    original = [_make_table("orders"), _make_table("items")]
    path = save_history(original, "prod", directory=str(tmp_path), timestamp="20240101T000000Z")
    profile, captured_at, tables = load_history(path)
    assert profile == "prod"
    assert len(tables) == 2
    assert {t.name for t in tables} == {"orders", "items"}


def test_list_history_empty(tmp_path):
    result = list_history(directory=str(tmp_path))
    assert result == []


def test_list_history_returns_files(tmp_path):
    for ts in ["20240101T000000Z", "20240102T000000Z"]:
        save_history([_make_table()], "prod", directory=str(tmp_path), timestamp=ts)
    files = list_history(directory=str(tmp_path))
    assert len(files) == 2
    assert all(f.endswith(".json") for f in files)


def test_list_history_sorted(tmp_path):
    timestamps = ["20240103T000000Z", "20240101T000000Z", "20240102T000000Z"]
    for ts in timestamps:
        save_history([_make_table()], "prod", directory=str(tmp_path), timestamp=ts)
    files = list_history(directory=str(tmp_path))
    basenames = [os.path.basename(f) for f in files]
    assert basenames == sorted(basenames)
