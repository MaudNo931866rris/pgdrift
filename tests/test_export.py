"""Tests for pgdrift.export."""
import json

import pytest

from pgdrift.diff import ColumnDiff, DriftReport, TableDiff
from pgdrift.export import export, export_csv, export_json


def _make_report(has_drift: bool = True) -> DriftReport:
    if not has_drift:
        return DriftReport(source_env="prod", target_env="staging", table_diffs=[], has_drift=False)

    col_diff = ColumnDiff(column_name="email", detail="type changed: varchar -> text")
    td_modified = TableDiff(
        schema="public",
        table="users",
        status="modified",
        column_diffs=[col_diff],
    )
    td_added = TableDiff(
        schema="public",
        table="audit_log",
        status="added",
        column_diffs=[],
    )
    return DriftReport(
        source_env="prod",
        target_env="staging",
        table_diffs=[td_modified, td_added],
        has_drift=True,
    )


class TestExportCsv:
    def test_csv_has_header(self):
        out = export_csv(_make_report())
        assert out.startswith("source,target,schema,table,status,column,detail")

    def test_csv_contains_modified_row(self):
        out = export_csv(_make_report())
        assert "users" in out
        assert "email" in out
        assert "type changed" in out

    def test_csv_contains_added_table_row(self):
        out = export_csv(_make_report())
        assert "audit_log" in out
        assert "added" in out

    def test_csv_no_drift_only_header(self):
        out = export_csv(_make_report(has_drift=False))
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 1  # header only


class TestExportJson:
    def test_json_is_valid(self):
        out = export_json(_make_report())
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_json_drift_detected_true(self):
        data = json.loads(export_json(_make_report()))
        assert data["drift_detected"] is True

    def test_json_drift_detected_false(self):
        data = json.loads(export_json(_make_report(has_drift=False)))
        assert data["drift_detected"] is False

    def test_json_contains_changes(self):
        data = json.loads(export_json(_make_report()))
        tables = [r["table"] for r in data["changes"]]
        assert "users" in tables
        assert "audit_log" in tables

    def test_json_env_names(self):
        data = json.loads(export_json(_make_report()))
        assert data["source"] == "prod"
        assert data["target"] == "staging"


class TestExportDispatch:
    def test_dispatch_csv(self):
        out = export(_make_report(), "csv")
        assert "source,target" in out

    def test_dispatch_json(self):
        out = export(_make_report(), "json")
        json.loads(out)  # must not raise

    def test_dispatch_unknown_raises(self):
        with pytest.raises(ValueError, match="Unsupported export format"):
            export(_make_report(), "xml")  # type: ignore[arg-type]
