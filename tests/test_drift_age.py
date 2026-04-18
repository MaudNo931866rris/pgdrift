"""Tests for pgdrift.drift_age."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from pgdrift.drift_age import DriftAgeEntry, compute_drift_age


def _ts(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _entry(table: str, days_ago: int, kind: str = "added_tables") -> dict:
    return {
        "captured_at": _ts(days_ago),
        "report": {
            kind: [{"table": table}],
            "added_tables": [],
            "removed_tables": [],
            "modified_tables": [],
        },
    }


def _make_entry(table: str, days_ago: int, kind: str = "added_tables") -> dict:
    base = {
        "captured_at": _ts(days_ago),
        "report": {
            "added_tables": [],
            "removed_tables": [],
            "modified_tables": [],
        },
    }
    base["report"][kind] = [{"table": table}]
    return base


def test_empty_audit_returns_empty_report():
    with patch("pgdrift.drift_age.load_audit", return_value=[]):
        report = compute_drift_age("prod")
    assert report.entries == []
    assert report.oldest() is None


def test_single_table_occurrence():
    audit = [_make_entry("public.users", 5)]
    with patch("pgdrift.drift_age.load_audit", return_value=audit):
        report = compute_drift_age("prod")
    assert len(report.entries) == 1
    e = report.entries[0]
    assert e.table == "public.users"
    assert e.occurrences == 1
    assert 4.5 < e.age_days < 5.5


def test_multiple_occurrences_same_table():
    audit = [
        _make_entry("public.orders", 10),
        _make_entry("public.orders", 3, kind="modified_tables"),
    ]
    with patch("pgdrift.drift_age.load_audit", return_value=audit):
        report = compute_drift_age("prod")
    assert len(report.entries) == 1
    e = report.entries[0]
    assert e.occurrences == 2
    assert e.age_days > 9


def test_multiple_tables():
    audit = [
        _make_entry("public.users", 7),
        _make_entry("public.orders", 2, kind="removed_tables"),
    ]
    with patch("pgdrift.drift_age.load_audit", return_value=audit):
        report = compute_drift_age("prod")
    assert len(report.entries) == 2
    tables = {e.table for e in report.entries}
    assert "public.users" in tables
    assert "public.orders" in tables


def test_oldest_returns_earliest_entry():
    audit = [
        _make_entry("public.users", 10),
        _make_entry("public.orders", 2),
    ]
    with patch("pgdrift.drift_age.load_audit", return_value=audit):
        report = compute_drift_age("prod")
    oldest = report.oldest()
    assert oldest is not None
    assert oldest.table == "public.users"


def test_as_dict_keys():
    audit = [_make_entry("public.items", 1)]
    with patch("pgdrift.drift_age.load_audit", return_value=audit):
        report = compute_drift_age("prod")
    d = report.as_dict()
    assert "entries" in d
    assert "age_days" in d["entries"][0]
    assert "occurrences" in d["entries"][0]
