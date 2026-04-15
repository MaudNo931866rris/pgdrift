"""Audit log: records every drift-check run with metadata and summary."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pgdrift.diff import DriftReport
from pgdrift.summary import compute_summary

_AUDIT_DIR = Path(os.environ.get("PGDRIFT_AUDIT_DIR", ".pgdrift/audit"))


def _audit_path(base_dir: Path = _AUDIT_DIR) -> Path:
    return base_dir


def _report_entry(source: str, target: str, report: DriftReport) -> dict:
    summary = compute_summary(report)
    return {
        "source": source,
        "target": target,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "has_drift": report.has_drift,
        "added_tables": len(report.added_tables),
        "removed_tables": len(report.removed_tables),
        "modified_tables": len(report.modified_tables),
        "severity": summary.severity,
        "total_changes": summary.total_changes,
    }


def save_audit(
    source: str,
    target: str,
    report: DriftReport,
    base_dir: Path = _AUDIT_DIR,
) -> Path:
    """Append a new audit entry and return the path of the written file."""
    directory = _audit_path(base_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    filename = directory / f"{timestamp}_{source}_vs_{target}.json"
    entry = _report_entry(source, target, report)
    filename.write_text(json.dumps(entry, indent=2))
    return filename


def load_audit(path: Path) -> dict:
    """Load a single audit entry from *path*."""
    return json.loads(path.read_text())


def list_audits(base_dir: Path = _AUDIT_DIR) -> List[Path]:
    """Return audit entry paths sorted oldest-first."""
    directory = _audit_path(base_dir)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def clear_audits(base_dir: Path = _AUDIT_DIR) -> int:
    """Delete all audit entries. Returns the count of deleted files."""
    files = list_audits(base_dir)
    for f in files:
        f.unlink()
    return len(files)
