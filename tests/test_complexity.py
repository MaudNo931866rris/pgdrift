import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.complexity import compute_complexity, TableComplexity, ComplexityReport


def _col(name: str, dtype: str, nullable: bool = False) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=dtype, nullable=nullable, default=None)


def _table(name: str, cols) -> TableSchema:
    return TableSchema(schema="public", name=name, columns=cols)


def test_empty_tables_returns_empty_report():
    report = compute_complexity([])
    assert report.entries == []
    assert report.average_score() == 0.0
    assert report.most_complex() is None


def test_single_table_score_nonzero():
    t = _table("users", [_col("id", "integer"), _col("email", "text", True)])
    report = compute_complexity([t])
    assert len(report.entries) == 1
    assert report.entries[0].score > 0


def test_nullable_increases_score():
    no_null = _table("a", [_col("id", "integer"), _col("name", "text")])
    all_null = _table("b", [_col("id", "integer", True), _col("name", "text", True)])
    r_no = compute_complexity([no_null])
    r_all = compute_complexity([all_null])
    assert r_all.entries[0].score > r_no.entries[0].score


def test_type_variety_counted():
    t = _table("x", [
        _col("a", "integer"),
        _col("b", "text"),
        _col("c", "boolean"),
    ])
    report = compute_complexity([t])
    assert report.entries[0].type_variety == 3


def test_most_complex_returns_highest_score():
    t1 = _table("simple", [_col("id", "integer")])
    t2 = _table("complex", [
        _col("a", "integer", True),
        _col("b", "text", True),
        _col("c", "boolean"),
        _col("d", "jsonb", True),
    ])
    report = compute_complexity([t1, t2])
    assert report.most_complex().full_name == "public.complex"


def test_as_dict_keys():
    t = _table("t", [_col("id", "integer")])
    report = compute_complexity([t])
    d = report.as_dict()
    assert "average_score" in d
    assert "tables" in d
    assert d["tables"][0]["table"] == "public.t"


def test_average_score_multiple_tables():
    t1 = _table("a", [_col("id", "integer")])
    t2 = _table("b", [_col("id", "integer"), _col("x", "text", True)])
    report = compute_complexity([t1, t2])
    expected = (report.entries[0].score + report.entries[1].score) / 2
    assert abs(report.average_score() - expected) < 1e-6
