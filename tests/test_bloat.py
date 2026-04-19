import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.bloat import compute_bloat, BloatReport


def _col(name: str, nullable: bool = False) -> ColumnInfo:
    return ColumnInfo(name=name, data_type="text", nullable=nullable)


def _table(name: str, columns: list) -> TableSchema:
    return TableSchema(schema="public", name=name, columns=columns)


def test_empty_tables_returns_empty_report():
    report = compute_bloat([])
    assert not report.any_bloat()
    assert report.entries == []


def test_clean_table_not_bloated():
    t = _table("users", [_col("id"), _col("name")])
    report = compute_bloat([t])
    assert not report.any_bloat()


def test_too_many_columns_flagged():
    cols = [_col(f"col_{i}") for i in range(35)]
    t = _table("fat", cols)
    report = compute_bloat([t], max_columns=30)
    assert report.any_bloat()
    entry = report.entries[0]
    assert entry.column_count == 35
    assert any("column count" in r for r in entry.reasons)


def test_high_nullable_ratio_flagged():
    cols = [_col(f"c{i}", nullable=(i > 0)) for i in range(10)]
    t = _table("nullable_heavy", cols)
    report = compute_bloat([t], max_nullable_ratio=0.5)
    assert report.any_bloat()
    entry = report.entries[0]
    assert any("nullable ratio" in r for r in entry.reasons)


def test_both_reasons_possible():
    cols = [_col(f"c{i}", nullable=True) for i in range(35)]
    t = _table("worst", cols)
    report = compute_bloat([t], max_columns=30, max_nullable_ratio=0.5)
    assert len(report.entries[0].reasons) == 2


def test_most_bloated_returns_top_n():
    tables = [
        _table("a", [_col(f"c{i}") for i in range(31)]),
        _table("b", [_col(f"c{i}") for i in range(40)]),
        _table("c", [_col(f"c{i}") for i in range(35)]),
    ]
    report = compute_bloat(tables, max_columns=30)
    top = report.most_bloated(2)
    assert len(top) == 2
    assert top[0].table == "public.b"


def test_as_dict_structure():
    cols = [_col(f"c{i}") for i in range(32)]
    t = _table("big", cols)
    report = compute_bloat([t])
    d = report.as_dict()
    assert "entries" in d
    assert d["entries"][0]["table"] == "public.big"
