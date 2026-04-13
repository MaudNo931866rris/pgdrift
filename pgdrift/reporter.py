"""HTML and Markdown report generation for drift results."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pgdrift.diff import DriftReport

ReportFormat = Literal["markdown", "html"]


def _md_table_diff(source: str, target: str, report: DriftReport) -> str:
    lines: list[str] = []
    for td in report.tables:
        if td.status == "added":
            lines.append(f"### Table `{td.table_name}` — added in **{target}**\n")
        elif td.status == "removed":
            lines.append(f"### Table `{td.table_name}` — removed from **{target}**\n")
        else:
            lines.append(f"### Table `{td.table_name}` — modified\n")
            lines.append("| Column | Change | Source | Target |")
            lines.append("|--------|--------|--------|--------|")
            for cd in td.columns:
                src_type = cd.source_type or ""
                tgt_type = cd.target_type or ""
                lines.append(f"| `{cd.column_name}` | {cd.status} | {src_type} | {tgt_type} |")
            lines.append("")
    return "\n".join(lines)


def render_markdown(source: str, target: str, report: DriftReport) -> str:
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = (
        f"# pgdrift Schema Drift Report\n\n"
        f"**Source:** `{source}`  \n**Target:** `{target}`  \n**Generated:** {ts}\n\n"
    )
    if not report.has_drift:
        return header + "_No schema drift detected._\n"
    return header + _md_table_diff(source, target, report)


def _html_rows(report: DriftReport) -> str:
    rows: list[str] = []
    for td in report.tables:
        status_color = {"added": "#c6efce", "removed": "#ffc7ce", "modified": "#ffeb9c"}.get(
            td.status, "#ffffff"
        )
        rows.append(
            f'<tr style="background:{status_color}">'
            f"<td><strong>{td.table_name}</strong></td>"
            f"<td>{td.status}</td>"
            f"<td>"
        )
        if td.columns:
            rows.append("<ul>")
            for cd in td.columns:
                rows.append(f"<li><code>{cd.column_name}</code>: {cd.status} "
                            f"({cd.source_type or 'n/a'} → {cd.target_type or 'n/a'})</li>")
            rows.append("</ul>")
        rows.append("</td></tr>")
    return "\n".join(rows)


def render_html(source: str, target: str, report: DriftReport) -> str:
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    drift_body = (
        "<p><em>No schema drift detected.</em></p>"
        if not report.has_drift
        else (
            "<table border='1' cellpadding='4' cellspacing='0'>"
            "<thead><tr><th>Table</th><th>Status</th><th>Column Changes</th></tr></thead>"
            f"<tbody>{_html_rows(report)}</tbody></table>"
        )
    )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>pgdrift Report</title></head><body>"
        f"<h1>pgdrift Schema Drift Report</h1>"
        f"<p><strong>Source:</strong> {source} &nbsp; "
        f"<strong>Target:</strong> {target} &nbsp; "
        f"<strong>Generated:</strong> {ts}</p>"
        f"{drift_body}</body></html>"
    )


def render(fmt: ReportFormat, source: str, target: str, report: DriftReport) -> str:
    if fmt == "html":
        return render_html(source, target, report)
    return render_markdown(source, target, report)
