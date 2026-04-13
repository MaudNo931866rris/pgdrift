"""Tests for pgdrift.snapshot."""

import json
import pytest
from pathlib import Path

from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.snapshot import save_snapshot, load_snapshot


def _make_table(schema: str, name: str) -> TableSchema:
    return TableSchema(
        schema=schema,
        name=name,
        columns=[
            ColumnInfo(name="id", data_type="integer", nullable=False, default="nextval('seq')"),
            ColumnInfo(name="email", data_type="text", nullable=True, default=None),
        ],
    )


@pytest.fixture()
def sample_tables():
    return {
        "public.users": _make_table("public", "users"),
        "public.orders": _make_table("public", "orders"),
    }


def test_save_creates_file(tmp_path, sample_tables):
    out = tmp_path / "snap.json"
    save_snapshot(sample_tables, out)
    assert out.exists()


def test_save_valid_json(tmp_path, sample_tables):
    out = tmp_path / "snap.json"
    save_snapshot(sample_tables, out)
    data = json.loads(out.read_text())
    assert "public.users" in data
    assert "public.orders" in data


def test_roundtrip_preserves_tables(tmp_path, sample_tables):
    out = tmp_path / "snap.json"
    save_snapshot(sample_tables, out)
    loaded = load_snapshot(out)
    assert set(loaded.keys()) == set(sample_tables.keys())


def test_roundtrip_preserves_columns(tmp_path, sample_tables):
    out = tmp_path / "snap.json"
    save_snapshot(sample_tables, out)
    loaded = load_snapshot(out)
    orig_cols = sample_tables["public.users"].columns
    loaded_cols = loaded["public.users"].columns
    assert len(loaded_cols) == len(orig_cols)
    assert loaded_cols[0].name == orig_cols[0].name
    assert loaded_cols[0].data_type == orig_cols[0].data_type
    assert loaded_cols[0].nullable == orig_cols[0].nullable
    assert loaded_cols[0].default == orig_cols[0].default


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Snapshot file not found"):
        load_snapshot(tmp_path / "nonexistent.json")
