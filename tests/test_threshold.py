"""Tests for pgdrift.threshold module."""

from __future__ import annotations

import pytest

from pgdrift.threshold import (
    ThresholdConfig,
    ThresholdResult,
    evaluate,
    load_threshold,
    save_threshold,
)
from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.inspector import ColumnInfo, TableSchema


def _make_col(name: str, dtype: str = "integer") -> ColumnInfo:
    return ColumnInfo(name=name, data_type=dtype, is_nullable=False)


def _make_table(name: str, schema: str = "public") -> TableSchema:
    return TableSchema(schema=schema, name=name, columns=[_make_col("id")])


def _empty_report() -> DriftReport:
    return DriftReport(source="src", target="tgt", added_tables=[], removed_tables=[], modified_tables=[])


def _drift_report() -> DriftReport:
    added = [_make_table("new_tbl")]
    removed = [_make_table("old_tbl")]
    mod = TableDiff(
        table=_make_table("users"),
        added_columns=[_make_col("email")],
        removed_columns=[_make_col("phone")],
        modified_columns=[],
    )
    return DriftReport(source="src", target="tgt", added_tables=added, removed_tables=removed, modified_tables=[mod])


def test_evaluate_passes_when_no_thresholds():
    result = evaluate(_drift_report(), ThresholdConfig())
    assert result.passed is True
    assert result.violations == []


def test_evaluate_passes_when_within_limits():
    config = ThresholdConfig(max_added_tables=2, max_removed_tables=2)
    result = evaluate(_drift_report(), config)
    assert result.passed is True


def test_evaluate_fails_added_tables():
    config = ThresholdConfig(max_added_tables=0)
    result = evaluate(_drift_report(), config)
    assert result.passed is False
    assert any("added tables" in v for v in result.violations)


def test_evaluate_fails_removed_tables():
    config = ThresholdConfig(max_removed_tables=0)
    result = evaluate(_drift_report(), config)
    assert result.passed is False
    assert any("removed tables" in v for v in result.violations)


def test_evaluate_fails_added_columns():
    config = ThresholdConfig(max_added_columns=0)
    result = evaluate(_drift_report(), config)
    assert result.passed is False
    assert any("added columns" in v for v in result.violations)


def test_evaluate_multiple_violations():
    config = ThresholdConfig(max_added_tables=0, max_removed_tables=0)
    result = evaluate(_drift_report(), config)
    assert result.passed is False
    assert len(result.violations) >= 2


def test_roundtrip_save_load(tmp_path):
    config = ThresholdConfig(max_added_tables=3, max_removed_columns=5)
    save_threshold(config, str(tmp_path))
    loaded = load_threshold(str(tmp_path))
    assert loaded.max_added_tables == 3
    assert loaded.max_removed_columns == 5


def test_load_returns_defaults_when_no_file(tmp_path):
    config = load_threshold(str(tmp_path))
    assert config.max_added_tables is None
    assert config.max_removed_tables is None
