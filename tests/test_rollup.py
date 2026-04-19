"""Tests for pgdrift.rollup."""
import pytest
from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.rollup import build_rollup, RollupReport, RollupEntry


def _report(source: str, target: str, diffs=None) -> DriftReport:
    return DriftReport(
        source_env=source,
        target_env=target,
        table_diffs=diffs or [],
    )


def _added_table(name="public.new_tbl") -> TableDiff:
    return TableDiff(table=name, added=True, removed=False, column_diffs=[])


def _removed_table(name="public.old_tbl") -> TableDiff:
    return TableDiff(table=name, added=False, removed=True, column_diffs=[])


def _modified_table(name="public.mod_tbl") -> TableDiff:
    col = ColumnDiff(column="col", change="modified", source_type="int", target_type="text")
    return TableDiff(table=name, added=False, removed=False, column_diffs=[col])


def test_empty_reports_returns_empty_rollup():
    rollup = build_rollup([])
    assert rollup.total_reports == 0
    assert rollup.grand_total_changes == 0
    assert not rollup.any_drift


def test_single_no_drift_report():
    rollup = build_rollup([_report("dev", "prod")])
    assert rollup.total_reports == 1
    assert rollup.grand_total_changes == 0
    assert not rollup.any_drift


def test_counts_added_tables():
    report = _report("dev", "prod", [_added_table()])
    rollup = build_rollup([report])
    assert rollup.entries[0].added_tables == 1
    assert rollup.entries[0].total_changes == 1


def test_counts_removed_tables():
    report = _report("dev", "prod", [_removed_table()])
    rollup = build_rollup([report])
    assert rollup.entries[0].removed_tables == 1


def test_counts_modified_tables():
    report = _report("dev", "prod", [_modified_table()])
    rollup = build_rollup([report])
    assert rollup.entries[0].modified_tables == 1


def test_multiple_reports_grand_total():
    r1 = _report("dev", "staging", [_added_table(), _removed_table()])
    r2 = _report("staging", "prod", [_modified_table()])
    rollup = build_rollup([r1, r2])
    assert rollup.total_reports == 2
    assert rollup.grand_total_changes == 3
    assert rollup.any_drift


def test_entry_preserves_env_names():
    rollup = build_rollup([_report("alpha", "beta")])
    assert rollup.entries[0].source == "alpha"
    assert rollup.entries[0].target == "beta"


def test_entry_count_matches_number_of_reports():
    """The number of entries in the rollup should equal the number of input reports."""
    reports = [
        _report("dev", "staging", [_added_table()]),
        _report("staging", "prod", [_removed_table()]),
        _report("prod", "dr", []),
    ]
    rollup = build_rollup(reports)
    assert len(rollup.entries) == len(reports)
