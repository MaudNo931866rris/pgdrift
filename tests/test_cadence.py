"""Tests for pgdrift.cadence."""
from __future__ import annotations

from pgdrift.cadence import CadenceEntry, CadenceReport, compute_cadence


def _rec(profile: str, captured_at: str) -> dict:
    return {"profile": profile, "captured_at": captured_at}


def test_empty_audit_returns_empty_report():
    report = compute_cadence([])
    assert report.is_empty()
    assert report.average_interval() == 0.0
    assert report.stddev_interval() == 0.0


def test_single_record_returns_empty_report():
    report = compute_cadence([_rec("prod", "2024-01-01T00:00:00")])
    assert report.is_empty()


def test_two_records_produces_one_entry():
    records = [
        _rec("prod", "2024-01-01T00:00:00"),
        _rec("prod", "2024-01-03T00:00:00"),
    ]
    report = compute_cadence(records)
    assert len(report.entries) == 1
    assert report.entries[0].interval_days == 2.0
    assert report.entries[0].profile == "prod"


def test_average_interval_calculated_correctly():
    records = [
        _rec("prod", "2024-01-01T00:00:00"),
        _rec("prod", "2024-01-03T00:00:00"),  # +2 days
        _rec("prod", "2024-01-07T00:00:00"),  # +4 days
    ]
    report = compute_cadence(records)
    assert len(report.entries) == 2
    assert report.average_interval() == 3.0


def test_stddev_zero_for_uniform_intervals():
    records = [
        _rec("prod", "2024-01-01T00:00:00"),
        _rec("prod", "2024-01-02T00:00:00"),
        _rec("prod", "2024-01-03T00:00:00"),
    ]
    report = compute_cadence(records)
    assert report.stddev_interval() == 0.0


def test_is_regular_true_for_uniform():
    records = [
        _rec("prod", "2024-01-01T00:00:00"),
        _rec("prod", "2024-01-02T00:00:00"),
        _rec("prod", "2024-01-03T00:00:00"),
    ]
    report = compute_cadence(records)
    assert report.is_regular()


def test_is_regular_false_for_erratic():
    records = [
        _rec("prod", "2024-01-01T00:00:00"),
        _rec("prod", "2024-01-02T00:00:00"),  # +1
        _rec("prod", "2024-01-20T00:00:00"),  # +18
    ]
    report = compute_cadence(records)
    assert not report.is_regular(tolerance=1.0)


def test_as_dict_contains_expected_keys():
    records = [
        _rec("prod", "2024-01-01T00:00:00"),
        _rec("prod", "2024-01-02T00:00:00"),
    ]
    report = compute_cadence(records)
    d = report.as_dict()
    assert "average_interval_days" in d
    assert "stddev_interval_days" in d
    assert "is_regular" in d
    assert "entries" in d
    assert len(d["entries"]) == 1


def test_records_sorted_by_captured_at():
    # Provide records out of order — should still compute correct interval
    records = [
        _rec("prod", "2024-01-05T00:00:00"),
        _rec("prod", "2024-01-01T00:00:00"),
    ]
    report = compute_cadence(records)
    assert len(report.entries) == 1
    assert report.entries[0].interval_days == 4.0
