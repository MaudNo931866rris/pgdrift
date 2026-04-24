"""Tests for pgdrift.redundancy."""
import pytest
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.redundancy import compute_redundancy, RedundancyReport


def _col(name: str, data_type: str = "text", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=data_type, nullable=nullable)


def _table(name: str, columns: list, schema: str = "public") -> TableSchema:
    return TableSchema(schema=schema, name=name, columns=columns)


# ---------------------------------------------------------------------------
# Basic cases
# ---------------------------------------------------------------------------

def test_empty_tables_returns_empty_report():
    report = compute_redundancy([])
    assert isinstance(report, RedundancyReport)
    assert not report.any_redundant()
    assert report.entries == []


def test_single_table_no_redundancy():
    t = _table("users", [_col("id", "integer"), _col("email", "text")])
    report = compute_redundancy([t])
    assert not report.any_redundant()


def test_shared_column_across_two_tables_detected():
    t1 = _table("users", [_col("created_at", "timestamp")])
    t2 = _table("orders", [_col("created_at", "timestamp")])
    report = compute_redundancy([t1, t2], min_occurrences=2)
    assert report.any_redundant()
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.column_name == "created_at"
    assert entry.data_type == "timestamp"
    assert entry.occurrence_count == 2
    assert "public.users" in entry.tables
    assert "public.orders" in entry.tables


def test_different_types_not_grouped_together():
    t1 = _table("a", [_col("status", "text")])
    t2 = _table("b", [_col("status", "integer")])
    report = compute_redundancy([t1, t2], min_occurrences=2)
    # each (name, type) pair only appears once — no redundancy
    assert not report.any_redundant()


def test_min_occurrences_threshold_respected():
    tables = [
        _table(f"t{i}", [_col("deleted_at", "timestamp")])
        for i in range(3)
    ]
    report2 = compute_redundancy(tables, min_occurrences=2)
    assert report2.any_redundant()
    report4 = compute_redundancy(tables, min_occurrences=4)
    assert not report4.any_redundant()


def test_most_redundant_returns_top_n():
    # "updated_at" appears in 4 tables; "name" appears in 2
    tables = [
        _table(f"t{i}", [_col("updated_at", "timestamp"), _col("name", "text")])
        for i in range(4)
    ] + [
        _table("extra", [_col("name", "text")])
    ]
    report = compute_redundancy(tables, min_occurrences=2)
    top = report.most_redundant(n=1)
    assert len(top) == 1
    assert top[0].column_name == "updated_at"


def test_as_dict_structure():
    t1 = _table("a", [_col("x", "text")])
    t2 = _table("b", [_col("x", "text")])
    report = compute_redundancy([t1, t2])
    d = report.as_dict()
    assert "entries" in d
    assert "total" in d
    assert d["total"] == 1
    assert d["entries"][0]["column_name"] == "x"
