"""Notification hooks for schema drift events."""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

from pgdrift.diff import DriftReport

logger = logging.getLogger(__name__)


@dataclass
class NotifyConfig:
    webhook_url: str
    on_drift_only: bool = True
    extra_headers: dict = field(default_factory=dict)


def _build_payload(report: DriftReport, source: str, target: str) -> dict:
    """Build a JSON-serialisable payload describing the drift report."""
    added = [t.table_name for t in report.added_tables]
    removed = [t.table_name for t in report.removed_tables]
    modified = [t.table_name for t in report.modified_tables]
    return {
        "source": source,
        "target": target,
        "has_drift": report.has_drift,
        "summary": {
            "added_tables": added,
            "removed_tables": removed,
            "modified_tables": modified,
        },
    }


def send_webhook(
    cfg: NotifyConfig,
    report: DriftReport,
    source: str,
    target: str,
) -> bool:
    """POST a drift payload to the configured webhook URL.

    Returns True on success, False on any HTTP or network error.
    """
    if cfg.on_drift_only and not report.has_drift:
        return True

    payload = _build_payload(report, source, target)
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", **cfg.extra_headers}

    req = urllib.request.Request(cfg.webhook_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except urllib.error.HTTPError as exc:
        logger.error("Webhook HTTP error: %s %s", exc.code, exc.reason)
        return False
    except urllib.error.URLError as exc:
        logger.error("Webhook URL error: %s", exc.reason)
        return False
    except OSError as exc:
        logger.error("Webhook network error: %s", exc)
        return False


def notify(
    report: DriftReport,
    source: str,
    target: str,
    webhook_url: Optional[str] = None,
    on_drift_only: bool = True,
) -> bool:
    """Convenience wrapper — build a NotifyConfig and call send_webhook."""
    if not webhook_url:
        return True
    cfg = NotifyConfig(webhook_url=webhook_url, on_drift_only=on_drift_only)
    return send_webhook(cfg, report, source, target)
