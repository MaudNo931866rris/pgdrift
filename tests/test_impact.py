"""Tests for pgdrift.impact."""
import pytest
from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.impact import compute_impact, ImpactReport


def _col_diff(name="col", removed=False, added=False, type_changed=False):
    return ColumnDiff(
        column_name=name,
        removed=removed,
        added=added,
        type_changed=type_changed,
        old_type="int" if type_changed else None,
        new_type="text" if type_changed else None,
        nullable_changed=False,
        old_nullable=None,
        new_nullable=None,
    )


def _report(*diffs):
    return DriftReport(source="src", target="tgt", table_diffs=list(diffs))


def test_no_drift_returns_empty_impact():
    r = _report()
    impact = compute_impact(r)
    assert isinstance(impact, ImpactReport)
    assert impact.items == []


def test_removed_table_is_critical():
    td = TableDiff(table_name="users", removed=True, added=False, column_diffs=[])
    impact = compute_impact(_report(td))
    assert len(impact.critical()) == 1
    assert impact.items[0].severity == "critical"


def test_added_table_is_low():
    td = TableDiff(table_name="logs", removed=False, added=True, column_diffs=[])
    impact = compute_impact(_report(td))
    assert impact.items[0].severity == "low"


def test_dropped_column_is_high():
    td = TableDiff(table_name="orders", removed=False, added=False,
                   column_diffs=[_col_diff("price", removed=True)])
    impact = compute_impact(_report(td))
    assert impact.items[0].severity == "high"


def test_type_change_is_medium():
    td = TableDiff(table_name="orders", removed=False, added=False,
                   column_diffs=[_col_diff("amount", type_changed=True)])
    impact = compute_impact(_report(td))
    assert impact.items[0].severity == "medium"


def test_as_dict_keys():
    td = TableDiff(table_name="t", removed=True, added=False, column_diffs=[])
    impact = compute_impact(_report(td))
    d = impact.as_dict()
    assert "items" in d
    assert "critical_count" in d
    assert d["critical_count"] == 1


def test_high_returns_correct_subset():
    t1 = TableDiff(table_name="a", removed=True, added=False, column_diffs=[])
    t2 = TableDiff(table_name="b", removed=False, added=False,
                   column_diffs=[_col_diff("x", removed=True)])
    impact = compute_impact(_report(t1, t2))
    assert len(impact.high()) == 1
    assert impact.high()[0].table == "b"
