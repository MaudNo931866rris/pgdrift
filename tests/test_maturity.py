"""Tests for pgdrift.maturity"""
import pytest
from pgdrift.maturity import compute_maturity, _grade, MaturityScore
from pgdrift.lint import LintResult, LintIssue
from pgdrift.drift_age import DriftAgeReport, DriftAgeEntry
from pgdrift.summary import DriftSummary


def _lint(errors=None, warnings=None) -> LintResult:
    issues = (errors or []) + (warnings or [])
    return LintResult(issues=issues)


def _err(msg="bad") -> LintIssue:
    return LintIssue(table="t", column=None, severity="error", message=msg)


def _warn(msg="meh") -> LintIssue:
    return LintIssue(table="t", column=None, severity="warning", message=msg)


def _age(days: int) -> DriftAgeReport:
    entry = DriftAgeEntry(table="t", first_seen="2024-01-01T00:00:00", last_seen="2024-01-01T00:00:00", age_days=days)
    return DriftAgeReport(entries=[entry])


def test_perfect_score_when_clean():
    result = compute_maturity("prod", _lint(), DriftAgeReport(entries=[]))
    assert result.score == 100.0
    assert result.grade == "A"
    assert result.penalties == []


def test_errors_reduce_score():
    result = compute_maturity("prod", _lint(errors=[_err(), _err()]), DriftAgeReport(entries=[]))
    assert result.score == 80.0
    assert len(result.penalties) == 1


def test_warnings_reduce_score():
    result = compute_maturity("prod", _lint(warnings=[_warn()]), DriftAgeReport(entries=[]))
    assert result.score == 95.0


def test_old_drift_reduces_score():
    result = compute_maturity("prod", _lint(), _age(60))
    assert result.score < 100.0
    assert any("drift unresolved" in p for p in result.penalties)


def test_fresh_drift_no_penalty():
    result = compute_maturity("prod", _lint(), _age(10))
    assert result.score == 100.0


def test_destructive_changes_penalty():
    summary = DriftSummary(total_changes=1, has_destructive_changes=True, severity="high", breakdown={})
    result = compute_maturity("prod", _lint(), DriftAgeReport(entries=[]), summary=summary)
    assert result.score == 90.0
    assert any("destructive" in p for p in result.penalties)


def test_grade_boundaries():
    assert _grade(100) == "A"
    assert _grade(75) == "B"
    assert _grade(60) == "C"
    assert _grade(40) == "D"
    assert _grade(39) == "F"


def test_as_dict_keys():
    result = compute_maturity("dev", _lint(), DriftAgeReport(entries=[]))
    d = result.as_dict()
    assert set(d.keys()) == {"profile", "score", "grade", "penalties"}


def test_score_clamped_to_zero():
    errs = [_err() for _ in range(20)]
    result = compute_maturity("prod", _lint(errors=errs), _age(365))
    assert result.score >= 0.0
