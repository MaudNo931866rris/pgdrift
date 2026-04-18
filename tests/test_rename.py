"""Tests for pgdrift.rename."""
import pytest
from pgdrift.rename import detect_renames, RenameReport
from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.inspector import ColumnInfo


def _col(name: str, data_type: str = "text", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name, data_type, nullable)


def _make_report(tables):
    return DriftReport(source="src", target="tgt", tables=tables)


def test_no_candidates_when_no_drift():
    report = _make_report([])
    result = detect_renames(report)
    assert not result.has_candidates()


def test_detects_table_rename():
    td_removed = TableDiff(table_name="public.users", added=False, removed=True, column_diffs=[])
    td_added = TableDiff(table_name="public.accounts", added=True, removed=False, column_diffs=[])
    report = _make_report([td_removed, td_added])
    result = detect_renames(report, threshold=0.4)
    assert result.has_candidates()
    candidate = result.candidates[0]
    assert candidate.kind == "table"
    assert candidate.old_name == "public.users"
    assert candidate.new_name == "public.accounts"


def test_no_table_rename_below_threshold():
    td_removed = TableDiff(table_name="public.orders", added=False, removed=True, column_diffs=[])
    td_added = TableDiff(table_name="public.xyz", added=True, removed=False, column_diffs=[])
    report = _make_report([td_removed, td_added])
    result = detect_renames(report, threshold=0.9)
    assert not result.has_candidates()


def test_detects_column_rename():
    col_removed = ColumnDiff(
        column_name="usr_name", added=False, removed=True,
        source_col=_col("usr_name"), target_col=None, changes={}
    )
    col_added = ColumnDiff(
        column_name="user_name", added=True, removed=False,
        source_col=None, target_col=_col("user_name"), changes={}
    )
    td = TableDiff(
        table_name="public.profiles",
        added=False, removed=False,
        column_diffs=[col_removed, col_added]
    )
    report = _make_report([td])
    result = detect_renames(report, threshold=0.6)
    assert result.has_candidates()
    c = result.candidates[0]
    assert c.kind == "column"
    assert c.table == "public.profiles"
    assert c.old_name == "usr_name"
    assert c.new_name == "user_name"


def test_as_dict_structure():
    col_removed = ColumnDiff(
        column_name="addr", added=False, removed=True,
        source_col=_col("addr"), target_col=None, changes={}
    )
    col_added = ColumnDiff(
        column_name="address", added=True, removed=False,
        source_col=None, target_col=_col("address"), changes={}
    )
    td = TableDiff(
        table_name="public.orders",
        added=False, removed=False,
        column_diffs=[col_removed, col_added]
    )
    report = _make_report([td])
    result = detect_renames(report, threshold=0.5)
    d = result.as_dict()
    assert "candidates" in d
    assert len(d["candidates"]) >= 1
    assert "score" in d["candidates"][0]
