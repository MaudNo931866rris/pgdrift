"""Tests for pgdrift.cohesion."""
import pytest

from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.cohesion import (
    CohesionEntry,
    CohesionReport,
    compute_cohesion,
    _prefix_groups,
    _cohesion_score,
)


def _col(name: str, dtype: str = "integer", nullable: bool = False) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=dtype, is_nullable=nullable)


def _table(name: str, cols) -> TableSchema:
    return TableSchema(
        schema="public",
        name=name,
        columns={c.name: c for c in cols},
    )


def test_empty_tables_returns_empty_report():
    report = compute_cohesion({})
    assert report.entries == []
    assert report.average_score() == 0.0


def test_single_type_single_prefix_high_cohesion():
    t = _table("orders", [_col("id"), _col("amount"), _col("total")])
    report = compute_cohesion({"public.orders": t})
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.score > 0.7


def test_many_types_lowers_cohesion():
    cols = [
        _col("id", "integer"),
        _col("name", "text"),
        _col("created", "timestamp"),
        _col("active", "boolean"),
        _col("ratio", "numeric"),
    ]
    t = _table("mixed", cols)
    report = compute_cohesion({"public.mixed": t})
    entry = report.entries[0]
    assert entry.type_variety == 5
    assert entry.score < 0.8


def test_prefix_groups_counted_correctly():
    names = ["user_id", "user_name", "order_id", "order_total", "status"]
    assert _prefix_groups(names) == 3  # user, order, status


def test_prefix_groups_empty():
    assert _prefix_groups([]) == 0


def test_cohesion_score_single_type_single_prefix():
    score = _cohesion_score(type_variety=1, prefix_groups=1, column_count=5)
    assert score == 1.0


def test_cohesion_score_clamped_to_zero():
    score = _cohesion_score(type_variety=100, prefix_groups=100, column_count=1)
    assert score >= 0.0


def test_least_cohesive_returns_sorted():
    t1 = _table("a", [_col("id")])
    t2 = _table("b", [_col("x", "text"), _col("y", "integer"), _col("z", "boolean")])
    report = compute_cohesion({"public.a": t1, "public.b": t2})
    least = report.least_cohesive(1)
    assert len(least) == 1
    assert least[0].table == "public.b"


def test_as_dict_structure():
    t = _table("t", [_col("id")])
    report = compute_cohesion({"public.t": t})
    d = report.as_dict()
    assert "average_score" in d
    assert "entries" in d
    assert d["entries"][0]["table"] == "public.t"
