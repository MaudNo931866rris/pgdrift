"""Tests for pgdrift.hotspot."""
import pytest
from pgdrift.hotspot import (
    HotspotEntry,
    HotspotReport,
    most_changed,
    as_dict,
    compute_hotspots,
)
from unittest.mock import patch


def _entry(table, count, cols=None):
    return HotspotEntry(table=table, change_count=count, column_changes=cols or {})


def test_most_changed_returns_top_n():
    report = HotspotReport(entries=[
        _entry("a", 3),
        _entry("b", 10),
        _entry("c", 1),
        _entry("d", 7),
    ])
    top = most_changed(report, n=2)
    assert [e.table for e in top] == ["b", "d"]


def test_most_changed_empty():
    assert most_changed(HotspotReport(), n=5) == []


def test_as_dict_structure():
    report = HotspotReport(entries=[_entry("users", 4, {"email": 2})])
    d = as_dict(report)
    assert "entries" in d
    assert d["entries"][0]["table"] == "users"
    assert d["entries"][0]["change_count"] == 4
    assert d["entries"][0]["column_changes"] == {"email": 2}


def test_compute_hotspots_counts_tables():
    fake_audit = [
        {"tables": [{"table": "orders", "column_diffs": [{"column": "status"}]}]},
        {"tables": [{"table": "orders", "column_diffs": [{"column": "total"}]},
                    {"table": "users", "column_diffs": []}]},
    ]
    with patch("pgdrift.hotspot.load_audit", return_value=fake_audit):
        report = compute_hotspots("prod")
    tables = {e.table: e.change_count for e in report.entries}
    assert tables["orders"] == 2
    assert tables["users"] == 1


def test_compute_hotspots_counts_columns():
    fake_audit = [
        {"tables": [{"table": "orders", "column_diffs": [{"column": "status"}, {"column": "status"}]}]},
    ]
    with patch("pgdrift.hotspot.load_audit", return_value=fake_audit):
        report = compute_hotspots("prod")
    e = next(x for x in report.entries if x.table == "orders")
    assert e.column_changes["status"] == 2


def test_compute_hotspots_empty_audit():
    with patch("pgdrift.hotspot.load_audit", return_value=[]):
        report = compute_hotspots("prod")
    assert report.entries == []
