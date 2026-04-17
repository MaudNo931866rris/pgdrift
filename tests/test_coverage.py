import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.coverage import TableCoverage, CoverageReport, compute_coverage


def _col(name: str, data_type: str = "text", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=data_type, nullable=nullable)


def _table(*col_names: str) -> TableSchema:
    cols = {n: _col(n) for n in col_names}
    return TableSchema(schema="public", name="t", columns=cols)


def test_identical_schemas_give_full_coverage():
    src = {"public.users": _table("id", "email")}
    tgt = {"public.users": _table("id", "email")}
    report = compute_coverage(src, tgt)
    assert report.overall_ratio == 1.0
    assert report.missing_tables == []


def test_missing_table_in_source():
    src = {}
    tgt = {"public.orders": _table("id", "total")}
    report = compute_coverage(src, tgt)
    assert "public.orders" in report.missing_tables
    assert report.overall_ratio == 0.0


def test_partial_column_coverage():
    src = {"public.users": _table("id")}
    tgt = {"public.users": _table("id", "email", "created_at")}
    report = compute_coverage(src, tgt)
    tc = report.tables[0]
    assert tc.matched_columns == 1
    assert tc.target_columns == 3
    assert pytest.approx(tc.ratio, 0.001) == 1 / 3


def test_empty_target_gives_full_coverage():
    report = compute_coverage({}, {})
    assert report.overall_ratio == 1.0
    assert report.tables == []


def test_as_dict_contains_expected_keys():
    src = {"public.items": _table("id", "name")}
    tgt = {"public.items": _table("id", "name", "price")}
    report = compute_coverage(src, tgt)
    d = report.as_dict()
    assert "overall_ratio" in d
    assert "missing_tables" in d
    assert "tables" in d
    assert d["tables"][0]["table"] == "public.items"


def test_table_coverage_ratio_zero_target_columns():
    tc = TableCoverage(table="x", source_columns=0, target_columns=0, matched_columns=0)
    assert tc.ratio == 1.0


def test_overall_ratio_averages_table_ratios():
    src = {
        "public.a": _table("id", "name"),
        "public.b": _table("id"),
    }
    tgt = {
        "public.a": _table("id", "name"),
        "public.b": _table("id", "value"),
    }
    report = compute_coverage(src, tgt)
    assert report.overall_ratio == pytest.approx(0.75, 0.001)
