"""Tests for pgdrift.churn."""
from unittest.mock import patch
from pgdrift.churn import compute_churn, ChurnReport, ChurnEntry


def _make_record(ts: str, added=(), removed=(), modified=()) -> dict:
    return {
        "captured_at": ts,
        "report": {
            "added_tables": list(added),
            "removed_tables": list(removed),
            "modified_tables": list(modified),
        },
    }


def test_empty_audit_returns_empty_report():
    with patch("pgdrift.churn.load_audit", return_value=[]):
        report = compute_churn("prod")
    assert isinstance(report, ChurnReport)
    assert report.entries == []


def test_single_change_creates_entry():
    records = [_make_record("2024-01-01T00:00:00", added=["public.users"])]
    with patch("pgdrift.churn.load_audit", return_value=records):
        report = compute_churn("prod")
    assert len(report.entries) == 1
    assert report.entries[0].table == "public.users"
    assert report.entries[0].change_count == 1


def test_multiple_changes_accumulate():
    records = [
        _make_record("2024-01-01T00:00:00", modified=["public.orders"]),
        _make_record("2024-01-02T00:00:00", modified=["public.orders"]),
        _make_record("2024-01-03T00:00:00", modified=["public.orders"]),
    ]
    with patch("pgdrift.churn.load_audit", return_value=records):
        report = compute_churn("prod")
    entry = report.entries[0]
    assert entry.change_count == 3
    assert entry.first_seen == "2024-01-01T00:00:00"
    assert entry.last_seen == "2024-01-03T00:00:00"


def test_most_churned_returns_top_n():
    entries = [ChurnEntry(table=f"t{i}", change_count=i, first_seen="", last_seen="") for i in range(10)]
    report = ChurnReport(entries=entries)
    top3 = report.most_churned(3)
    assert len(top3) == 3
    assert top3[0].change_count == 9


def test_as_dict_structure():
    records = [_make_record("2024-01-01T00:00:00", added=["public.items"])]
    with patch("pgdrift.churn.load_audit", return_value=records):
        report = compute_churn("prod")
    d = report.as_dict()
    assert "entries" in d
    assert d["entries"][0]["table"] == "public.items"


def test_removed_and_added_both_counted():
    records = [
        _make_record("2024-01-01T00:00:00", added=["public.a"], removed=["public.b"]),
    ]
    with patch("pgdrift.churn.load_audit", return_value=records):
        report = compute_churn("prod")
    tables = {e.table for e in report.entries}
    assert "public.a" in tables
    assert "public.b" in tables
