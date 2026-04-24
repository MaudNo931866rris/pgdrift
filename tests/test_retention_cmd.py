"""Tests for pgdrift.commands.retention_cmd."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from pgdrift.commands.retention_cmd import (
    cmd_retention_check,
    cmd_retention_set,
    cmd_retention_show,
)
from pgdrift.retention import RetentionPolicy, save_retention


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "snapshot_days": 90,
        "audit_days": 180,
        "json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _ts(days_ago: int) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def test_set_returns_0(tmp_path: Path) -> None:
    with patch("pgdrift.commands.retention_cmd._RETENTION_DIR", tmp_path):
        rc = cmd_retention_set(_args(snapshot_days=30, audit_days=60))
    assert rc == 0


def test_set_persists_policy(tmp_path: Path) -> None:
    with patch("pgdrift.commands.retention_cmd._RETENTION_DIR", tmp_path):
        cmd_retention_set(_args(snapshot_days=14, audit_days=28))
    data = json.loads((tmp_path / "retention.json").read_text())
    assert data["max_snapshot_days"] == 14
    assert data["max_audit_days"] == 28


def test_show_returns_0(tmp_path: Path, capsys) -> None:
    save_retention(tmp_path, RetentionPolicy(max_snapshot_days=45, max_audit_days=90))
    with patch("pgdrift.commands.retention_cmd._RETENTION_DIR", tmp_path):
        rc = cmd_retention_show(_args())
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["max_snapshot_days"] == 45


def test_check_no_violations_returns_0(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    snap_file = snap_dir / "fresh.json"
    snap_file.write_text(json.dumps({"captured_at": _ts(5), "tables": {}}))

    with (
        patch("pgdrift.commands.retention_cmd._RETENTION_DIR", tmp_path),
        patch("pgdrift.commands.retention_cmd._SNAPSHOT_DIR", snap_dir),
        patch("pgdrift.commands.retention_cmd._AUDIT_DIR", tmp_path / "audit"),
    ):
        rc = cmd_retention_check(_args())
    assert rc == 0


def test_check_with_violations_returns_1(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    old = snap_dir / "old.json"
    old.write_text(json.dumps({"captured_at": _ts(120), "tables": {}}))

    save_retention(tmp_path, RetentionPolicy(max_snapshot_days=30, max_audit_days=180))

    with (
        patch("pgdrift.commands.retention_cmd._RETENTION_DIR", tmp_path),
        patch("pgdrift.commands.retention_cmd._SNAPSHOT_DIR", snap_dir),
        patch("pgdrift.commands.retention_cmd._AUDIT_DIR", tmp_path / "audit"),
    ):
        rc = cmd_retention_check(_args())
    assert rc == 1


def test_check_json_flag_outputs_json(tmp_path: Path, capsys) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()

    with (
        patch("pgdrift.commands.retention_cmd._RETENTION_DIR", tmp_path),
        patch("pgdrift.commands.retention_cmd._SNAPSHOT_DIR", snap_dir),
        patch("pgdrift.commands.retention_cmd._AUDIT_DIR", tmp_path / "audit"),
    ):
        rc = cmd_retention_check(_args(json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "policy" in data
    assert "violations" in data
    assert rc == 0
