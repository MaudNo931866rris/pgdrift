"""Tests for pgdrift.retention."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pgdrift.retention import (
    RetentionPolicy,
    RetentionReport,
    evaluate_retention,
    load_retention,
    save_retention,
)


def _ts(days_ago: int) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


@pytest.fixture()
def ret_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_returns_defaults_when_no_file(ret_dir: Path) -> None:
    policy = load_retention(ret_dir)
    assert policy.max_snapshot_days == 90
    assert policy.max_audit_days == 180


def test_save_and_load_roundtrip(ret_dir: Path) -> None:
    policy = RetentionPolicy(max_snapshot_days=30, max_audit_days=60)
    save_retention(ret_dir, policy)
    loaded = load_retention(ret_dir)
    assert loaded.max_snapshot_days == 30
    assert loaded.max_audit_days == 60


def test_save_creates_file(ret_dir: Path) -> None:
    save_retention(ret_dir, RetentionPolicy())
    assert (ret_dir / "retention.json").exists()


def test_no_violations_when_fresh() -> None:
    policy = RetentionPolicy(max_snapshot_days=90, max_audit_days=180)
    snapshots = [{"name": "snap1", "captured_at": _ts(10)}]
    audits = [{"profile": "prod", "captured_at": _ts(20)}]
    report = evaluate_retention(policy, snapshots, audits)
    assert not report.any_violations()
    assert report.violations == []


def test_old_snapshot_is_violation() -> None:
    policy = RetentionPolicy(max_snapshot_days=30, max_audit_days=180)
    snapshots = [{"name": "old_snap", "captured_at": _ts(45)}]
    report = evaluate_retention(policy, snapshots, [])
    assert report.any_violations()
    assert len(report.violations) == 1
    v = report.violations[0]
    assert v.kind == "snapshot"
    assert v.name == "old_snap"
    assert v.age_days >= 45


def test_old_audit_is_violation() -> None:
    policy = RetentionPolicy(max_snapshot_days=90, max_audit_days=60)
    audits = [{"profile": "staging", "captured_at": _ts(90)}]
    report = evaluate_retention(policy, [], audits)
    assert report.any_violations()
    assert report.violations[0].kind == "audit"


def test_as_dict_structure() -> None:
    policy = RetentionPolicy(max_snapshot_days=45, max_audit_days=90)
    report = evaluate_retention(policy, [], [])
    d = report.as_dict()
    assert "policy" in d
    assert d["policy"]["max_snapshot_days"] == 45
    assert "violations" in d
    assert isinstance(d["violations"], list)


def test_invalid_timestamp_skipped() -> None:
    policy = RetentionPolicy(max_snapshot_days=1, max_audit_days=1)
    snapshots = [{"name": "bad", "captured_at": "not-a-date"}]
    report = evaluate_retention(policy, snapshots, [])
    assert not report.any_violations()
