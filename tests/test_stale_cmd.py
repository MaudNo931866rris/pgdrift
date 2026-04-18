"""Tests for pgdrift.commands.stale_cmd."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pgdrift.commands.stale_cmd import cmd_stale


def _args(snapshot_dir: str, max_age_days: float = 7.0) -> argparse.Namespace:
    return argparse.Namespace(snapshot_dir=snapshot_dir, max_age_days=max_age_days)


def _write(directory: Path, name: str, profile: str, captured_at: datetime) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(
        json.dumps({"profile": profile, "captured_at": captured_at.isoformat(), "tables": []})
    )


def test_no_snapshots_returns_0(tmp_path: Path) -> None:
    rc = cmd_stale(_args(str(tmp_path / "empty")))
    assert rc == 0


def test_fresh_snapshots_returns_0(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write(tmp_path, "snap.json", "dev", now - timedelta(days=1))
    rc = cmd_stale(_args(str(tmp_path)))
    assert rc == 0


def test_stale_snapshot_returns_1(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write(tmp_path, "snap.json", "prod", now - timedelta(days=30))
    rc = cmd_stale(_args(str(tmp_path)))
    assert rc == 1


def test_mixed_returns_1(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write(tmp_path, "fresh.json", "dev", now - timedelta(days=1))
    _write(tmp_path, "old.json", "prod", now - timedelta(days=20))
    rc = cmd_stale(_args(str(tmp_path)))
    assert rc == 1


def test_custom_max_age(tmp_path: Path) -> None:
    now = datetime.now(tz=timezone.utc)
    _write(tmp_path, "snap.json", "prod", now - timedelta(days=2))
    assert cmd_stale(_args(str(tmp_path), max_age_days=1.0)) == 1
    assert cmd_stale(_args(str(tmp_path), max_age_days=30.0)) == 0
