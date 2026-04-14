"""Tests for pgdrift.notify."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pgdrift.diff import DriftReport, TableDiff
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.notify import NotifyConfig, _build_payload, notify, send_webhook


def _make_table(name: str) -> TableSchema:
    col = ColumnInfo(column_name="id", data_type="integer", is_nullable=False)
    return TableSchema(schema="public", table_name=name, columns=[col])


@pytest.fixture()
def no_drift_report() -> DriftReport:
    return DriftReport(source="dev", target="prod", added_tables=[], removed_tables=[], modified_tables=[])


@pytest.fixture()
def drift_report() -> DriftReport:
    td = TableDiff(
        table_name="users",
        added_columns=[],
        removed_columns=[],
        modified_columns=[],
    )
    return DriftReport(source="dev", target="prod", added_tables=[_make_table("orders")], removed_tables=[], modified_tables=[td])


def test_build_payload_no_drift(no_drift_report):
    payload = _build_payload(no_drift_report, "dev", "prod")
    assert payload["has_drift"] is False
    assert payload["source"] == "dev"
    assert payload["target"] == "prod"
    assert payload["summary"]["added_tables"] == []


def test_build_payload_with_drift(drift_report):
    payload = _build_payload(drift_report, "dev", "prod")
    assert payload["has_drift"] is True
    assert "orders" in payload["summary"]["added_tables"]
    assert "users" in payload["summary"]["modified_tables"]


def test_send_webhook_skips_when_no_drift_and_on_drift_only(no_drift_report):
    cfg = NotifyConfig(webhook_url="http://example.com/hook", on_drift_only=True)
    with patch("urllib.request.urlopen") as mock_open:
        result = send_webhook(cfg, no_drift_report, "dev", "prod")
    assert result is True
    mock_open.assert_not_called()


def test_send_webhook_posts_when_drift(drift_report):
    cfg = NotifyConfig(webhook_url="http://example.com/hook", on_drift_only=True)
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        result = send_webhook(cfg, drift_report, "dev", "prod")
    assert result is True
    mock_open.assert_called_once()
    req = mock_open.call_args[0][0]
    body = json.loads(req.data)
    assert body["has_drift"] is True


def test_send_webhook_returns_false_on_error(drift_report):
    import urllib.error
    cfg = NotifyConfig(webhook_url="http://bad.example/hook")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = send_webhook(cfg, drift_report, "dev", "prod")
    assert result is False


def test_notify_returns_true_when_no_url(no_drift_report):
    assert notify(no_drift_report, "dev", "prod", webhook_url=None) is True


def test_notify_sends_when_url_provided(drift_report):
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = notify(drift_report, "dev", "prod", webhook_url="http://example.com/hook")
    assert result is True
