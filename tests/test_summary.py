"""Tests for pgdrift.summary module."""

import pytest

from pgdrift.diff import ColumnDiff, DriftReport, TableDiff
from pgdrift.summary import DriftSummary, compute_summary, format_summary


def _make_report(
    added_tables=None,
    removed_tables=None,
    modified_tables=None,
) -> DriftReport:
    return DriftReport(
        source="prod",
        target="staging",
        added_tables=added_tables or [],
        removed_tables=removed_tables or [],
        modified_tables=modified_tables or [],
    )


def _table_diff(
    name="public.users",
    added_cols=None,
    removed_cols=None,
    modified_cols=None,
) -> TableDiff:
    return TableDiff(
        table=name,
        added_columns=added_cols or [],
        removed_columns=removed_cols or [],
        modified_columns=modified_cols or [],
    )


def test_no_drift_gives_none_severity():
    report = _make_report()
    summary = compute_summary(report)
    assert summary.severity == "none"
    assert summary.total_changes == 0


def test_added_table_low_severity():
    report = _make_report(added_tables=["public.orders"])
    summary = compute_summary(report)
    assert summary.added_tables == 1
    assert summary.severity == "low"


def test_removed_table_high_severity():
    report = _make_report(removed_tables=["public.legacy"])
    summary = compute_summary(report)
    assert summary.removed_tables == 1
    assert summary.severity == "high"


def test_removed_column_high_severity():
    td = _table_diff(removed_cols=["email"])
    report = _make_report(modified_tables=[td])
    summary = compute_summary(report)
    assert summary.removed_columns == 1
    assert summary.severity == "high"


def test_many_changes_medium_severity():
    td = _table_diff(
        added_cols=[f"col{i}" for i in range(10)],
    )
    report = _make_report(modified_tables=[td])
    summary = compute_summary(report)
    assert summary.total_changes >= 10
    assert summary.severity == "medium"


def test_column_counts_aggregated_across_tables():
    td1 = _table_diff(added_cols=["a", "b"], modified_cols=["c"])
    td2 = _table_diff(added_cols=["x"])
    report = _make_report(modified_tables=[td1, td2])
    summary = compute_summary(report)
    assert summary.added_columns == 3
    assert summary.modified_columns == 1


def test_format_summary_contains_source_and_target():
    report = _make_report()
    summary = compute_summary(report)
    text = format_summary(summary)
    assert "prod" in text
    assert "staging" in text


def test_format_summary_contains_severity():
    report = _make_report(removed_tables=["public.old"])
    summary = compute_summary(report)
    text = format_summary(summary)
    assert "HIGH" in text


def test_total_changes_sums_all_fields():
    summary = DriftSummary(
        source="a",
        target="b",
        added_tables=1,
        removed_tables=2,
        modified_tables=3,
        added_columns=4,
        removed_columns=5,
        modified_columns=6,
        severity="high",
    )
    assert summary.total_changes == 21
