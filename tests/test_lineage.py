"""Tests for pgdrift.lineage."""

from __future__ import annotations

import pytest
from pgdrift.lineage import (
    LineageEvent, LineageReport, save_lineage, load_lineage, list_lineage, build_lineage,
)
from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.inspector import ColumnInfo


@pytest.fixture()
def lineage_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _event(event="added", table="public.users", column="email"):
    return LineageEvent(event=event, table=table, column=column,
                        snapshot="snap1", captured_at="2024-01-01T00:00:00")


def test_load_returns_none_when_missing(lineage_dir):
    assert load_lineage("nonexistent") is None


def test_save_creates_file(lineage_dir):
    report = LineageReport(events=[_event()])
    path = save_lineage(report, "snap1")
    assert path.exists()


def test_roundtrip_preserves_events(lineage_dir):
    report = LineageReport(events=[_event("added"), _event("removed", column="name")])
    save_lineage(report, "snap1")
    loaded = load_lineage("snap1")
    assert loaded is not None
    assert len(loaded.events) == 2
    assert loaded.events[0].event == "added"


def test_list_returns_labels(lineage_dir):
    save_lineage(LineageReport(events=[_event()]), "alpha")
    save_lineage(LineageReport(events=[_event()]), "beta")
    labels = list_lineage()
    assert "alpha" in labels
    assert "beta" in labels


def test_for_table_filters_correctly(lineage_dir):
    report = LineageReport(events=[
        _event(table="public.users"),
        _event(table="public.orders"),
    ])
    result = report.for_table("public.users")
    assert len(result) == 1
    assert result[0].table == "public.users"


def test_for_column_filters_correctly():
    report = LineageReport(events=[
        _event(column="email"),
        _event(column="name"),
    ])
    result = report.for_column("public.users", "email")
    assert len(result) == 1


def test_build_lineage_from_drift_report():
    col = ColumnInfo(column_name="email", data_type="text", is_nullable=False)
    td = TableDiff(
        table_name="public.users",
        added_columns=[col],
        removed_columns=[],
        modified_columns=[],
    )
    drift = DriftReport(source="dev", target="prod", table_diffs=[td], added_tables=[], removed_tables=[])
    report = build_lineage(drift, "snap1", "2024-01-01T00:00:00")
    assert len(report.events) == 1
    assert report.events[0].event == "added"
    assert report.events[0].column == "email"
