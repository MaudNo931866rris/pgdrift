"""Tests for pgdrift.formatter."""

import pytest

from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.formatter import format_report


def make_report(table_diffs=None, source="dev", target="prod"):
    return DriftReport(
        source_env=source,
        target_env=target,
        table_diffs=table_diffs or [],
    )


def test_no_drift_message():
    report = make_report()
    output = format_report(report, use_color=False)
    assert "No drift detected" in output


def test_header_contains_env_names():
    report = make_report(source="staging", target="production")
    output = format_report(report, use_color=False)
    assert "staging" in output
    assert "production" in output


def test_added_table_shown():
    diff = TableDiff(table_name="users", status="added", column_diffs=[])
    report = make_report(table_diffs=[diff])
    output = format_report(report, use_color=False)
    assert "users" in output
    assert "added" in output


def test_removed_table_shown():
    diff = TableDiff(table_name="legacy", status="removed", column_diffs=[])
    report = make_report(table_diffs=[diff])
    output = format_report(report, use_color=False)
    assert "legacy" in output
    assert "removed" in output


def test_changed_column_shown():
    col = ColumnDiff(name="email", status="changed", source_type="varchar", target_type="text")
    diff = TableDiff(table_name="users", status="changed", column_diffs=[col])
    report = make_report(table_diffs=[diff])
    output = format_report(report, use_color=False)
    assert "email" in output
    assert "varchar" in output
    assert "text" in output


def test_color_codes_present_when_enabled():
    diff = TableDiff(table_name="orders", status="added", column_diffs=[])
    report = make_report(table_diffs=[diff])
    output = format_report(report, use_color=True)
    assert "\033[" in output


def test_no_color_codes_when_disabled():
    diff = TableDiff(table_name="orders", status="added", column_diffs=[])
    report = make_report(table_diffs=[diff])
    output = format_report(report, use_color=False)
    assert "\033[" not in output
