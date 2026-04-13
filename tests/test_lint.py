"""Tests for pgdrift.lint module."""

import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.lint import lint_tables, LintIssue, LintResult


def _make_table(name: str, columns: list[ColumnInfo], schema: str = "public") -> TableSchema:
    return TableSchema(schema=schema, name=name, columns=columns)


def _col(name: str, data_type: str = "text", nullable: bool = False) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=data_type, nullable=nullable)


def test_no_issues_for_clean_table():
    table = _make_table("users", [_col("id", "integer"), _col("email", "text", nullable=False)])
    result = lint_tables([table])
    assert not result.has_issues


def test_missing_id_column_raises_warning():
    table = _make_table("orders", [_col("order_ref", "text")])
    result = lint_tables([table])
    rules = [i.rule for i in result.issues]
    assert "missing_primary_key" in rules


def test_nullable_identity_column_raises_warning():
    table = _make_table(
        "users",
        [_col("id", "integer"), _col("email", "text", nullable=True)],
    )
    result = lint_tables([table])
    rules = [i.rule for i in result.issues]
    assert "nullable_identity_column" in rules


def test_generic_column_name_raises_warning():
    table = _make_table("things", [_col("id"), _col("data", "jsonb")])
    result = lint_tables([table])
    rules = [i.rule for i in result.issues]
    assert "generic_column_name" in rules


def test_multiple_issues_on_single_table():
    table = _make_table(
        "stuff",
        [_col("value", "text"), _col("email", "text", nullable=True)],
    )
    result = lint_tables([table])
    assert len(result.issues) >= 2


def test_lint_result_warnings_property():
    issues = [
        LintIssue(table="t", column=None, rule="r1", message="m1", severity="warning"),
        LintIssue(table="t", column=None, rule="r2", message="m2", severity="error"),
    ]
    result = LintResult(issues=issues)
    assert len(result.warnings) == 1
    assert len(result.errors) == 1


def test_lint_result_has_issues_false_when_empty():
    result = LintResult(issues=[])
    assert not result.has_issues


def test_issue_includes_table_full_name():
    table = _make_table("accounts", [_col("ref", "text")], schema="billing")
    result = lint_tables([table])
    assert any("billing.accounts" in i.table for i in result.issues)
