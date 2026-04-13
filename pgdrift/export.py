"""Export drift reports to CSV or JSON formats."""
from __future__ import annotations

import csv
import io
import json
from typing import Literal

from pgdrift.diff import DriftReport

ExportFormat = Literal["csv", "json"]


def _report_to_records(report: DriftReport) -> list[dict]:
    """Flatten a DriftReport into a list of row dicts."""
    rows: list[dict] = []
    for td in report.table_diffs:
        if td.status in ("added", "removed"):
            rows.append(
                {
                    "source": report.source_env,
                    "target": report.target_env,
                    "schema": td.schema,
                    "table": td.table,
                    "status": td.status,
                    "column": "",
                    "detail": "",
                }
            )
        else:
            for cd in td.column_diffs:
                rows.append(
                    {
                        "source": report.source_env,
                        "target": report.target_env,
                        "schema": td.schema,
                        "table": td.table,
                        "status": td.status,
                        "column": cd.column_name,
                        "detail": cd.detail,
                    }
                )
    return rows


def export_csv(report: DriftReport) -> str:
    """Render a DriftReport as a CSV string."""
    records = _report_to_records(report)
    output = io.StringIO()
    fieldnames = ["source", "target", "schema", "table", "status", "column", "detail"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def export_json(report: DriftReport) -> str:
    """Render a DriftReport as a JSON string."""
    records = _report_to_records(report)
    payload = {
        "source": report.source_env,
        "target": report.target_env,
        "drift_detected": report.has_drift,
        "changes": records,
    }
    return json.dumps(payload, indent=2)


def export(report: DriftReport, fmt: ExportFormat) -> str:
    """Dispatch to the correct exporter based on *fmt*."""
    if fmt == "csv":
        return export_csv(report)
    if fmt == "json":
        return export_json(report)
    raise ValueError(f"Unsupported export format: {fmt!r}")
