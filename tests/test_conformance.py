"""Tests for pgdrift.conformance."""
import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.conformance import (
    compute_conformance,
    ConformanceReport,
    ConformanceViolation,
    _is_snake_case,
)


def _col(name: str, data_type: str = "text", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=data_type, nullable=nullable)


def _table(name: str, columns=None) -> TableSchema:
    return TableSchema(
        schema="public",
        name=name,
        columns=columns or [_col("id", "integer", False)],
    )


# ---------------------------------------------------------------------------
# _is_snake_case
# ---------------------------------------------------------------------------

def test_snake_case_valid():
    assert _is_snake_case("my_table") is True


def test_snake_case_rejects_uppercase():
    assert _is_snake_case("MyTable") is False


def test_snake_case_rejects_leading_underscore():
    assert _is_snake_case("_private") is False


def test_snake_case_rejects_empty_string():
    assert _is_snake_case("") is False


# ---------------------------------------------------------------------------
# compute_conformance
# ---------------------------------------------------------------------------

def test_no_violations_for_clean_schema():
    tables = [_table("users"), _table("order_items")]
    report = compute_conformance(tables)
    assert not report.any_violations
    assert report.violation_count == 0


def test_camel_case_table_name_flagged():
    tables = [_table("OrderItems")]
    report = compute_conformance(tables)
    rules = [v.rule for v in report.violations]
    assert "snake_case_table" in rules


def test_camel_case_column_flagged():
    tables = [_table("orders", columns=[_col("OrderDate")])]
    report = compute_conformance(tables)
    rules = [v.rule for v in report.violations]
    assert "snake_case_column" in rules


def test_id_column_wrong_type_flagged():
    tables = [_table("users", columns=[_col("id", "varchar", False)])]
    report = compute_conformance(tables)
    rules = [v.rule for v in report.violations]
    assert "id_column_type" in rules


def test_id_column_uuid_not_flagged():
    tables = [_table("users", columns=[_col("id", "uuid", False)])]
    report = compute_conformance(tables)
    id_violations = [v for v in report.violations if v.rule == "id_column_type"]
    assert len(id_violations) == 0


def test_as_dict_structure():
    tables = [_table("BadName", columns=[_col("id", "varchar")])]
    report = compute_conformance(tables)
    d = report.as_dict()
    assert "violation_count" in d
    assert "any_violations" in d
    assert "violations" in d
    assert isinstance(d["violations"], list)


def test_multiple_violations_counted():
    tables = [
        _table("BadTable", columns=[_col("BadColumn"), _col("id", "text")]),
    ]
    report = compute_conformance(tables)
    assert report.violation_count >= 3
