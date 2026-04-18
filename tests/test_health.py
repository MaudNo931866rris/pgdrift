"""Tests for pgdrift.health."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pgdrift.diff import DriftReport, TableDiff
from pgdrift.health import HealthReport, _overall_grade, compute_health
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.lint import LintResult


def _col(name="id", dtype="integer", nullable=False):
    return ColumnInfo(name=name, data_type=dtype, is_nullable=nullable)


def _table(name="users", schema="public"):
    return TableSchema(schema=schema, name=name, columns=[_col()])


def _empty_report():
    return DriftReport(source="src", target="tgt", table_diffs=[])


def _lint(errors=0, warnings=0):
    issues = []
    from pgdrift.lint import LintIssue
    for _ in range(errors):
        issues.append(LintIssue(table="t", column=None, level="error", message="e"))
    for _ in range(warnings):
        issues.append(LintIssue(table="t", column=None, level="warning", message="w"))
    return LintResult(issues=issues)


def test_overall_grade_a():
    assert _overall_grade(95.0, _lint()) == "A"


def test_overall_grade_b():
    assert _overall_grade(80.0, _lint()) == "B"


def test_overall_grade_degrades_with_errors():
    # 95 - 5*4 = 75 → B
    assert _overall_grade(95.0, _lint(errors=4)) == "B"


def test_overall_grade_f_with_many_errors():
    assert _overall_grade(50.0, _lint(errors=10)) == "F"


def test_compute_health_returns_health_report():
    tables = [_table()]
    report = _empty_report()
    with patch("pgdrift.health.run_lint") as mock_lint:
        mock_lint.return_value = _lint()
        health = compute_health("prod", report, tables)
    assert isinstance(health, HealthReport)
    assert health.profile == "prod"
    assert health.grade in {"A", "B", "C", "D", "F"}


def test_as_dict_keys():
    tables = [_table()]
    report = _empty_report()
    with patch("pgdrift.health.run_lint") as mock_lint:
        mock_lint.return_value = _lint()
        health = compute_health("prod", report, tables)
    d = health.as_dict()
    for key in ("profile", "grade", "score", "lint_errors", "lint_warnings", "total_changes", "has_destructive"):
        assert key in d


def test_no_changes_gives_zero_total():
    tables = [_table()]
    report = _empty_report()
    with patch("pgdrift.health.run_lint") as mock_lint:
        mock_lint.return_value = _lint()
        health = compute_health("prod", report, tables)
    assert health.as_dict()["total_changes"] == 0
