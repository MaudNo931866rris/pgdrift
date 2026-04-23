"""Tests for pgdrift.skew."""
import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.skew import compute_skew, SkewReport, SkewEntry, as_dict


def _col(name: str) -> ColumnInfo:
    return ColumnInfo(name=name, data_type="text", is_nullable=True)


def _table(name: str, ncols: int) -> TableSchema:
    return TableSchema(
        schema="public",
        name=name,
        columns=[_col(f"col{i}") for i in range(ncols)],
    )


def test_empty_tables_returns_empty_report():
    report = compute_skew([])
    assert report.entries == []
    assert report.mean_columns == 0.0
    assert report.stddev == 0.0


def test_single_table_has_zero_deviation():
    report = compute_skew([_table("users", 5)])
    assert len(report.entries) == 1
    assert report.entries[0].deviation == 0.0
    assert report.mean_columns == 5.0


def test_uniform_tables_have_zero_stddev():
    tables = [_table(f"t{i}", 4) for i in range(5)]
    report = compute_skew(tables)
    assert report.stddev == 0.0
    for entry in report.entries:
        assert entry.deviation == 0.0


def test_outlier_detected():
    # one table with 50 cols, others with 5
    tables = [_table(f"t{i}", 5) for i in range(9)] + [_table("fat", 50)]
    report = compute_skew(tables)
    assert report.any_skew(threshold=2.0)
    outliers = report.outliers(threshold=2.0)
    assert len(outliers) == 1
    assert outliers[0].table == "public.fat"


def test_entries_sorted_by_abs_deviation():
    tables = [
        _table("small", 2),
        _table("medium", 10),
        _table("large", 30),
    ]
    report = compute_skew(tables)
    devs = [abs(e.deviation) for e in report.entries]
    assert devs == sorted(devs, reverse=True)


def test_no_skew_below_threshold():
    tables = [_table(f"t{i}", 5 + i) for i in range(4)]
    report = compute_skew(tables)
    assert not report.any_skew(threshold=2.0)


def test_as_dict_structure():
    entry = SkewEntry(table="public.users", column_count=10, deviation=1.23456)
    d = as_dict(entry)
    assert d["table"] == "public.users"
    assert d["column_count"] == 10
    assert d["deviation"] == 1.2346
