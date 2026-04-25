"""Tests for pgdrift.volatility."""
import json
import os
import pytest

from pgdrift.volatility import (
    VolatilityEntry,
    VolatilityReport,
    compute_volatility,
)


def _write_audit(tmp_path, records):
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    for i, record in enumerate(records):
        (audit_dir / f"audit_{i:04d}.json").write_text(json.dumps(record))
    return str(audit_dir)


def test_empty_audit_returns_empty_report(tmp_path):
    audit_dir = str(tmp_path / "audit")
    os.makedirs(audit_dir, exist_ok=True)
    report = compute_volatility(audit_dir)
    assert report.is_empty()
    assert report.average_score() == 0.0


def test_single_unchanged_table_scores_zero(tmp_path):
    records = [
        {
            "captured_at": "2024-01-01T00:00:00",
            "report": {"tables": [{"table": "public.users", "status": "unchanged"}]},
        }
    ]
    audit_dir = _write_audit(tmp_path, records)
    report = compute_volatility(audit_dir)
    assert len(report.entries) == 1
    assert report.entries[0].volatility_score == 0.0
    assert report.entries[0].change_count == 0


def test_always_changed_table_scores_one(tmp_path):
    records = [
        {
            "captured_at": f"2024-01-0{i+1}T00:00:00",
            "report": {"tables": [{"table": "public.orders", "status": "modified"}]},
        }
        for i in range(3)
    ]
    audit_dir = _write_audit(tmp_path, records)
    report = compute_volatility(audit_dir)
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.table == "public.orders"
    assert entry.change_count == 3
    assert entry.snapshots_seen == 3
    assert entry.volatility_score == pytest.approx(1.0)


def test_partial_volatility_score(tmp_path):
    records = [
        {"captured_at": "2024-01-01T00:00:00", "report": {"tables": [{"table": "public.items", "status": "modified"}]}},
        {"captured_at": "2024-01-02T00:00:00", "report": {"tables": [{"table": "public.items", "status": "unchanged"}]}},
        {"captured_at": "2024-01-03T00:00:00", "report": {"tables": [{"table": "public.items", "status": "unchanged"}]}},
        {"captured_at": "2024-01-04T00:00:00", "report": {"tables": [{"table": "public.items", "status": "modified"}]}},
    ]
    audit_dir = _write_audit(tmp_path, records)
    report = compute_volatility(audit_dir)
    entry = report.entries[0]
    assert entry.change_count == 2
    assert entry.snapshots_seen == 4
    assert entry.volatility_score == pytest.approx(0.5)


def test_most_volatile_returns_top_n(tmp_path):
    records = [
        {"captured_at": "t1", "report": {"tables": [
            {"table": "a", "status": "modified"},
            {"table": "b", "status": "unchanged"},
        ]}},
    ]
    audit_dir = _write_audit(tmp_path, records)
    report = compute_volatility(audit_dir)
    top = report.most_volatile(n=1)
    assert len(top) == 1
    assert top[0].table == "a"


def test_as_dict_structure(tmp_path):
    records = [
        {"captured_at": "t1", "report": {"tables": [{"table": "x", "status": "added"}]}},
    ]
    audit_dir = _write_audit(tmp_path, records)
    report = compute_volatility(audit_dir)
    d = report.as_dict()
    assert "average_volatility_score" in d
    assert "entries" in d
    assert d["entries"][0]["table"] == "x"


def test_record_without_report_key_skipped(tmp_path):
    records = [
        {"captured_at": "t1"},
        {"captured_at": "t2", "report": {"tables": [{"table": "public.log", "status": "modified"}]}},
    ]
    audit_dir = _write_audit(tmp_path, records)
    report = compute_volatility(audit_dir)
    assert len(report.entries) == 1
