"""Tests for pgdrift.obsolete."""
import pytest
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.diff import compute_drift
from pgdrift.obsolete import compute_obsolete, ObsoleteReport


def _col(name: str, dtype: str = "text", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=dtype, is_nullable=nullable)


def _table(schema: str, name: str, cols: list) -> TableSchema:
    return TableSchema(schema=schema, table=name, columns=cols)


def test_no_obsolete_when_identical():
    t = _table("public", "users", [_col("id", "int")])
    report = compute_drift([t], [t])
    obs = compute_obsolete(report)
    assert not obs.any_obsolete()
    assert obs.entries == []


def test_removed_column_is_obsolete():
    source = _table("public", "users", [_col("id", "int"), _col("email", "text")])
    target = _table("public", "users", [_col("id", "int")])
    report = compute_drift([source], [target])
    obs = compute_obsolete(report)
    assert obs.any_obsolete()
    assert len(obs.entries) == 1
    e = obs.entries[0]
    assert e.column == "email"
    assert e.data_type == "text"
    assert e.schema == "public"
    assert e.table == "users"


def test_added_column_not_obsolete():
    source = _table("public", "orders", [_col("id", "int")])
    target = _table("public", "orders", [_col("id", "int"), _col("total", "numeric")])
    report = compute_drift([source], [target])
    obs = compute_obsolete(report)
    assert not obs.any_obsolete()


def test_by_table_filters_correctly():
    source = _table("public", "users", [_col("id"), _col("bio")])
    target = _table("public", "users", [_col("id")])
    report = compute_drift([source], [target])
    obs = compute_obsolete(report)
    assert len(obs.by_table("public", "users")) == 1
    assert obs.by_table("public", "orders") == []


def test_as_dict_structure():
    source = _table("app", "items", [_col("id"), _col("name")])
    target = _table("app", "items", [_col("id")])
    report = compute_drift([source], [target])
    obs = compute_obsolete(report)
    d = obs.as_dict()
    assert "entries" in d
    assert d["entries"][0]["column"] == "name"
    assert d["entries"][0]["table"] == "items"
