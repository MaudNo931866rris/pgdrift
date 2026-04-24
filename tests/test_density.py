"""Tests for pgdrift.density."""
from __future__ import annotations

import pytest

from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.density import (
    DensityEntry,
    DensityReport,
    compute_density,
    _density_score,
)


def _col(name: str, nullable: bool = False) -> ColumnInfo:
    return ColumnInfo(name=name, data_type="text", nullable=nullable)


def _table(name: str, columns: list) -> TableSchema:
    return TableSchema(schema="public", name=name, columns=columns)


# ---------------------------------------------------------------------------
# _density_score
# ---------------------------------------------------------------------------

def test_density_score_all_required():
    assert _density_score(4, 4) == 1.0


def test_density_score_all_nullable():
    assert _density_score(4, 0) == 0.0


def test_density_score_half():
    assert _density_score(4, 2) == 0.5


def test_density_score_zero_columns():
    assert _density_score(0, 0) == 0.0


# ---------------------------------------------------------------------------
# compute_density
# ---------------------------------------------------------------------------

def test_empty_tables_returns_empty_report():
    report = compute_density([])
    assert report.entries == []


def test_single_table_all_required():
    t = _table("users", [_col("id"), _col("email"), _col("name")])
    report = compute_density([t])
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.density_score == 1.0
    assert entry.nullable_columns == 0
    assert entry.non_nullable_columns == 3


def test_single_table_mixed_nullability():
    cols = [_col("id"), _col("bio", nullable=True), _col("avatar", nullable=True)]
    t = _table("profiles", cols)
    report = compute_density([t])
    entry = report.entries[0]
    assert entry.total_columns == 3
    assert entry.non_nullable_columns == 1
    assert entry.nullable_columns == 2
    assert abs(entry.density_score - 1 / 3) < 1e-9


def test_average_score_multiple_tables():
    t1 = _table("a", [_col("x"), _col("y")])
    t2 = _table("b", [_col("x", nullable=True), _col("y", nullable=True)])
    report = compute_density([t1, t2])
    assert report.average_score() == 0.5


def test_least_dense_ordering():
    t1 = _table("a", [_col("x"), _col("y")])
    t2 = _table("b", [_col("x", nullable=True), _col("y", nullable=True)])
    t3 = _table("c", [_col("x"), _col("y", nullable=True)])
    report = compute_density([t1, t2, t3])
    least = report.least_dense(2)
    assert least[0].table == "public.b"


def test_most_dense_ordering():
    t1 = _table("a", [_col("x"), _col("y")])
    t2 = _table("b", [_col("x", nullable=True), _col("y", nullable=True)])
    report = compute_density([t1, t2])
    most = report.most_dense(1)
    assert most[0].table == "public.a"


def test_as_dict_structure():
    t = _table("orders", [_col("id"), _col("note", nullable=True)])
    report = compute_density([t])
    d = report.as_dict()
    assert "average_score" in d
    assert "entries" in d
    assert d["entries"][0]["table"] == "public.orders"
