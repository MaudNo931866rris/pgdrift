"""Tests for pgdrift.compare."""
from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.compare import compare_against_baseline, compare_against_snapshot


def _make_table(name: str) -> TableSchema:
    return TableSchema(
        schema="public",
        name=name,
        columns=[ColumnInfo(name="id", data_type="integer", is_nullable=False)],
    )


def test_compare_against_baseline_returns_none_when_missing(tmp_path):
    live = {"public.users": _make_table("users")}
    result = compare_against_baseline(live, "prod", "v1", baselines_dir=str(tmp_path))
    assert result is None


def test_compare_against_baseline_no_drift(tmp_path):
    from pgdrift.baseline import save_baseline
    table = _make_table("users")
    live = {"public.users": table}
    save_baseline("prod", "v1", live, baselines_dir=str(tmp_path))
    result = compare_against_baseline(live, "prod", "v1", baselines_dir=str(tmp_path))
    assert result is not None
    assert not result.report.has_drift
    assert result.reference_type == "baseline"


def test_compare_against_baseline_detects_drift(tmp_path):
    from pgdrift.baseline import save_baseline
    old = {"public.users": _make_table("users")}
    save_baseline("prod", "v1", old, baselines_dir=str(tmp_path))
    new = {"public.users": _make_table("users"), "public.orders": _make_table("orders")}
    result = compare_against_baseline(new, "prod", "v1", baselines_dir=str(tmp_path))
    assert result is not None
    assert result.report.has_drift


def test_compare_against_snapshot_returns_none_when_missing(tmp_path):
    live = {"public.users": _make_table("users")}
    result = compare_against_snapshot(live, "prod", str(tmp_path / "missing.json"))
    assert result is None


def test_compare_against_snapshot_no_drift(tmp_path):
    from pgdrift.snapshot import save_snapshot
    table = _make_table("users")
    live = {"public.users": table}
    path = str(tmp_path / "snap.json")
    save_snapshot(live, path)
    result = compare_against_snapshot(live, "prod", path)
    assert result is not None
    assert not result.report.has_drift
    assert result.reference_type == "snapshot"
