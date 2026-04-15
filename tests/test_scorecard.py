"""Tests for pgdrift.scorecard."""
import pytest
from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.scorecard import compute_scorecard, _grade, ScorecardResult


def _empty_report() -> DriftReport:
    return DriftReport(
        source="prod",
        target="staging",
        added_tables=[],
        removed_tables=[],
        modified_tables=[],
    )


def _table_diff(added=0, removed=0, modified=0) -> TableDiff:
    return TableDiff(
        schema="public",
        table="t",
        added_columns=[ColumnDiff(name=f"a{i}", source=None, target="int") for i in range(added)],
        removed_columns=[ColumnDiff(name=f"r{i}", source="int", target=None) for i in range(removed)],
        modified_columns=[ColumnDiff(name=f"m{i}", source="int", target="text") for i in range(modified)],
    )


def test_perfect_score_when_no_drift():
    report = _empty_report()
    card = compute_scorecard(report, total_tables=5)
    assert card.score == 100.0
    assert card.grade == "A"


def test_score_decreases_with_added_tables():
    report = _empty_report()
    report.added_tables.append("public.new_table")
    card = compute_scorecard(report, total_tables=5)
    assert card.score < 100.0


def test_score_decreases_with_removed_tables():
    report = _empty_report()
    report.removed_tables.append("public.old_table")
    card = compute_scorecard(report, total_tables=5)
    assert card.score < 100.0


def test_score_decreases_with_column_changes():
    report = _empty_report()
    report.modified_tables.append(_table_diff(modified=3))
    card = compute_scorecard(report, total_tables=5)
    assert card.score < 100.0


def test_score_never_below_zero():
    report = _empty_report()
    for i in range(20):
        report.removed_tables.append(f"public.t{i}")
    card = compute_scorecard(report, total_tables=5)
    assert card.score >= 0.0


def test_score_never_above_100():
    report = _empty_report()
    card = compute_scorecard(report, total_tables=1)
    assert card.score <= 100.0


def test_result_fields_populated():
    report = _empty_report()
    report.modified_tables.append(_table_diff(added=1, removed=1, modified=2))
    card = compute_scorecard(report, total_tables=3)
    assert card.source == "prod"
    assert card.target == "staging"
    assert card.total_column_changes == 4
    assert isinstance(card.grade, str)


def test_as_dict_contains_expected_keys():
    card = compute_scorecard(_empty_report(), total_tables=2)
    d = card.as_dict()
    for key in ("source", "target", "score", "grade", "added_tables", "removed_tables"):
        assert key in d


@pytest.mark.parametrize("score,expected", [
    (95, "A"), (80, "B"), (65, "C"), (50, "D"), (30, "F")
])
def test_grade_boundaries(score, expected):
    assert _grade(score) == expected
