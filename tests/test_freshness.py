"""Tests for pgdrift.freshness."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pgdrift.freshness import FreshnessReport, compute_freshness


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    d = tmp_path / "snapshots"
    d.mkdir()
    return d


def _write(snap_dir: Path, name: str, profile: str, captured_at: datetime) -> None:
    data = {"profile": profile, "captured_at": captured_at.isoformat(), "tables": {}}
    (snap_dir / name).write_text(json.dumps(data))


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_empty_dir_returns_empty_report(snap_dir: Path) -> None:
    report = compute_freshness(snapshot_dir=snap_dir, now=NOW)
    assert isinstance(report, FreshnessReport)
    assert report.entries == []


def test_fresh_snapshot_is_fresh(snap_dir: Path) -> None:
    _write(snap_dir, "prod.json", "prod", NOW - timedelta(hours=1))
    report = compute_freshness(snapshot_dir=snap_dir, max_age_hours=24.0, now=NOW)
    assert len(report.entries) == 1
    assert report.entries[0].is_fresh is True
    assert report.entries[0].profile == "prod"


def test_old_snapshot_is_stale(snap_dir: Path) -> None:
    _write(snap_dir, "prod.json", "prod", NOW - timedelta(hours=48))
    report = compute_freshness(snapshot_dir=snap_dir, max_age_hours=24.0, now=NOW)
    assert report.entries[0].is_fresh is False
    assert report.any_stale() is True


def test_stale_entries_filters_correctly(snap_dir: Path) -> None:
    _write(snap_dir, "fresh.json", "dev", NOW - timedelta(hours=2))
    _write(snap_dir, "stale.json", "prod", NOW - timedelta(hours=30))
    report = compute_freshness(snapshot_dir=snap_dir, max_age_hours=24.0, now=NOW)
    stale = report.stale_entries()
    assert len(stale) == 1
    assert stale[0].profile == "prod"


def test_missing_dir_returns_empty(tmp_path: Path) -> None:
    report = compute_freshness(snapshot_dir=tmp_path / "nonexistent", now=NOW)
    assert report.entries == []
    assert report.any_stale() is False


def test_age_hours_calculated_correctly(snap_dir: Path) -> None:
    _write(snap_dir, "s.json", "staging", NOW - timedelta(hours=5, minutes=30))
    report = compute_freshness(snapshot_dir=snap_dir, max_age_hours=24.0, now=NOW)
    assert abs(report.entries[0].age_hours - 5.5) < 0.01


def test_invalid_json_skipped(snap_dir: Path) -> None:
    (snap_dir / "bad.json").write_text("not json")
    report = compute_freshness(snapshot_dir=snap_dir, now=NOW)
    assert report.entries == []
