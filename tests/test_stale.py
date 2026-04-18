"""Tests for pgdrift.stale."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pgdrift.stale import check_stale


def _write_snapshot(directory: Path, name: str, profile: str, captured_at: datetime) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    data = {"profile": profile, "captured_at": captured_at.isoformat(), "tables": []}
    (directory / name).write_text(json.dumps(data))


def test_empty_dir_returns_empty_report(tmp_path: Path) -> None:
    report = check_stale(tmp_path / "missing", max_age_days=7)
    assert report.entries == []
    assert not report.any_stale()


def test_fresh_snapshot_not_stale(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write_snapshot(tmp_path, "snap.json", "prod", now - timedelta(days=1))
    report = check_stale(tmp_path, max_age_days=7)
    assert len(report.entries) == 1
    assert not report.entries[0].is_stale
    assert not report.any_stale()


def test_old_snapshot_is_stale(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write_snapshot(tmp_path, "snap.json", "prod", now - timedelta(days=10))
    report = check_stale(tmp_path, max_age_days=7)
    assert report.entries[0].is_stale
    assert report.any_stale()


def test_stale_entries_filters_correctly(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write_snapshot(tmp_path, "fresh.json", "dev", now - timedelta(days=2))
    _write_snapshot(tmp_path, "old.json", "prod", now - timedelta(days=14))
    report = check_stale(tmp_path, max_age_days=7)
    assert len(report.stale_entries()) == 1
    assert report.stale_entries()[0].profile == "prod"


def test_snapshot_missing_captured_at_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text(json.dumps({"profile": "x", "tables": []}))
    report = check_stale(tmp_path, max_age_days=7)
    assert report.entries == []


def test_age_days_is_approximate(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write_snapshot(tmp_path, "snap.json", "staging", now - timedelta(days=3))
    report = check_stale(tmp_path, max_age_days=7)
    assert 2.9 < report.entries[0].age_days < 3.1
