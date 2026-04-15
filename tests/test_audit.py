"""Tests for pgdrift.audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pgdrift.audit import clear_audits, list_audits, load_audit, save_audit
from pgdrift.diff import ColumnDiff, DriftReport, TableDiff
from pgdrift.inspector import ColumnInfo, TableSchema


def _make_column(name: str = "id", col_type: str = "integer", nullable: bool = False) -> ColumnInfo:
    return ColumnInfo(name=name, col_type=col_type, nullable=nullable)


def _empty_report() -> DriftReport:
    return DriftReport(source="prod", target="staging", added_tables=[], removed_tables=[], modified_tables=[])


def _drift_report() -> DriftReport:
    table = TableSchema(schema="public", name="users", columns=[_make_column()])
    td = TableDiff(
        table_name="public.users",
        added_columns=[],
        removed_columns=[_make_column("email", "text")],
        modified_columns=[],
    )
    return DriftReport(
        source="prod",
        target="staging",
        added_tables=[],
        removed_tables=[],
        modified_tables=[td],
    )


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def test_save_creates_file(audit_dir: Path) -> None:
    path = save_audit("prod", "staging", _empty_report(), base_dir=audit_dir)
    assert path.exists()


def test_save_file_is_valid_json(audit_dir: Path) -> None:
    path = save_audit("prod", "staging", _empty_report(), base_dir=audit_dir)
    data = json.loads(path.read_text())
    assert isinstance(data, dict)


def test_save_contains_source_and_target(audit_dir: Path) -> None:
    path = save_audit("prod", "staging", _empty_report(), base_dir=audit_dir)
    data = load_audit(path)
    assert data["source"] == "prod"
    assert data["target"] == "staging"


def test_save_no_drift_report(audit_dir: Path) -> None:
    path = save_audit("prod", "staging", _empty_report(), base_dir=audit_dir)
    data = load_audit(path)
    assert data["has_drift"] is False
    assert data["total_changes"] == 0


def test_save_drift_report_reflects_changes(audit_dir: Path) -> None:
    path = save_audit("prod", "staging", _drift_report(), base_dir=audit_dir)
    data = load_audit(path)
    assert data["has_drift"] is True
    assert data["modified_tables"] == 1


def test_list_returns_empty_when_no_dir(audit_dir: Path) -> None:
    assert list_audits(audit_dir) == []


def test_list_returns_saved_entries(audit_dir: Path) -> None:
    save_audit("prod", "staging", _empty_report(), base_dir=audit_dir)
    save_audit("prod", "dev", _empty_report(), base_dir=audit_dir)
    assert len(list_audits(audit_dir)) == 2


def test_clear_removes_all_entries(audit_dir: Path) -> None:
    save_audit("prod", "staging", _empty_report(), base_dir=audit_dir)
    save_audit("prod", "dev", _empty_report(), base_dir=audit_dir)
    count = clear_audits(audit_dir)
    assert count == 2
    assert list_audits(audit_dir) == []
