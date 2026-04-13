"""Tests for pgdrift.reporter module."""
from __future__ import annotations

import pytest

from pgdrift.diff import ColumnDiff, DriftReport, TableDiff
from pgdrift.reporter import render_html, render_markdown, render


SOURCE = "prod"
TARGET = "staging"


def _no_drift_report() -> DriftReport:
    return DriftReport(tables=[])


def _drift_report() -> DriftReport:
    return DriftReport(
        tables=[
            TableDiff(
                table_name="users",
                status="modified",
                columns=[
                    ColumnDiff(
                        column_name="email",
                        status="modified",
                        source_type="varchar(100)",
                        target_type="text",
                    )
                ],
            ),
            TableDiff(table_name="orders", status="added", columns=[]),
            TableDiff(table_name="legacy", status="removed", columns=[]),
        ]
    )


# ── Markdown ──────────────────────────────────────────────────────────────────

def test_markdown_no_drift_contains_no_drift_message():
    md = render_markdown(SOURCE, TARGET, _no_drift_report())
    assert "No schema drift detected" in md


def test_markdown_contains_source_and_target():
    md = render_markdown(SOURCE, TARGET, _no_drift_report())
    assert SOURCE in md
    assert TARGET in md


def test_markdown_added_table():
    md = render_markdown(SOURCE, TARGET, _drift_report())
    assert "orders" in md
    assert "added" in md


def test_markdown_removed_table():
    md = render_markdown(SOURCE, TARGET, _drift_report())
    assert "legacy" in md
    assert "removed" in md


def test_markdown_column_diff_in_table():
    md = render_markdown(SOURCE, TARGET, _drift_report())
    assert "email" in md
    assert "varchar(100)" in md
    assert "text" in md


# ── HTML ──────────────────────────────────────────────────────────────────────

def test_html_no_drift_message():
    html = render_html(SOURCE, TARGET, _no_drift_report())
    assert "No schema drift detected" in html


def test_html_contains_table_tag():
    html = render_html(SOURCE, TARGET, _drift_report())
    assert "<table" in html


def test_html_shows_modified_table():
    html = render_html(SOURCE, TARGET, _drift_report())
    assert "users" in html
    assert "modified" in html


# ── render() dispatcher ───────────────────────────────────────────────────────

def test_render_markdown_dispatch():
    out = render("markdown", SOURCE, TARGET, _no_drift_report())
    assert out.startswith("# pgdrift")


def test_render_html_dispatch():
    out = render("html", SOURCE, TARGET, _no_drift_report())
    assert "<!DOCTYPE html>" in out
