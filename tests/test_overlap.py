"""Tests for pgdrift.overlap."""
import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.overlap import OverlapEntry, OverlapReport, compute_overlap


def _col(name: str) -> ColumnInfo:
    return ColumnInfo(name=name, data_type="text", is_nullable=True)


def _table(schema: str, name: str, cols) -> TableSchema:
    return TableSchema(schema=schema, name=name, columns=cols)


def _make_schemas():
    src = {
        "public.users": _table("public", "users", [_col("id"), _col("email"), _col("name")]),
        "public.orders": _table("public", "orders", [_col("id"), _col("total")]),
    }
    tgt = {
        "public.users": _table("public", "users", [_col("id"), _col("email"), _col("phone")]),
        "public.orders": _table("public", "orders", [_col("id"), _col("total")]),
    }
    return src, tgt


def test_compute_overlap_returns_common_tables():
    src, tgt = _make_schemas()
    report = compute_overlap(src, tgt)
    tables = [e.table for e in report.entries]
    assert "public.users" in tables
    assert "public.orders" in tables


def test_shared_columns_detected():
    src, tgt = _make_schemas()
    report = compute_overlap(src, tgt)
    users = next(e for e in report.entries if e.table == "public.users")
    assert "id" in users.shared_columns
    assert "email" in users.shared_columns


def test_source_only_columns():
    src, tgt = _make_schemas()
    report = compute_overlap(src, tgt)
    users = next(e for e in report.entries if e.table == "public.users")
    assert "name" in users.source_only


def test_target_only_columns():
    src, tgt = _make_schemas()
    report = compute_overlap(src, tgt)
    users = next(e for e in report.entries if e.table == "public.users")
    assert "phone" in users.target_only


def test_identical_table_full_overlap():
    src, tgt = _make_schemas()
    report = compute_overlap(src, tgt)
    orders = next(e for e in report.entries if e.table == "public.orders")
    assert orders.overlap_ratio() == 1.0
    assert not orders.source_only
    assert not orders.target_only


def test_any_divergence_true_when_diff():
    src, tgt = _make_schemas()
    report = compute_overlap(src, tgt)
    assert report.any_divergence() is True


def test_any_divergence_false_when_identical():
    src = {"public.t": _table("public", "t", [_col("id")])}
    tgt = {"public.t": _table("public", "t", [_col("id")])}
    report = compute_overlap(src, tgt)
    assert report.any_divergence() is False


def test_as_dict_structure():
    src, tgt = _make_schemas()
    report = compute_overlap(src, tgt)
    d = report.as_dict()
    assert "entries" in d
    assert "any_divergence" in d
    assert "overlap_ratio" in d["entries"][0]


def test_non_common_tables_excluded():
    src = {
        "public.users": _table("public", "users", [_col("id")]),
        "public.extra": _table("public", "extra", [_col("id")]),
    }
    tgt = {"public.users": _table("public", "users", [_col("id")])}
    report = compute_overlap(src, tgt)
    tables = [e.table for e in report.entries]
    assert "public.extra" not in tables
