"""Resolution tracking: record when drift issues are acknowledged or resolved."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_RESOLUTION_DIR = Path(".pgdrift") / "resolutions"


def _resolution_path(profile: str) -> Path:
    return _RESOLUTION_DIR / f"{profile}.json"


@dataclass
class ResolutionEntry:
    table: str
    column: Optional[str]
    reason: str
    resolved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_by: str = "unknown"

    def key(self) -> str:
        return f"{self.table}.{self.column}" if self.column else self.table


@dataclass
class ResolutionReport:
    entries: List[ResolutionEntry] = field(default_factory=list)

    def by_table(self, table: str) -> List[ResolutionEntry]:
        return [e for e in self.entries if e.table == table]

    def is_resolved(self, table: str, column: Optional[str] = None) -> bool:
        key = f"{table}.{column}" if column else table
        return any(e.key() == key for e in self.entries)


def load_resolutions(profile: str) -> ResolutionReport:
    path = _resolution_path(profile)
    if not path.exists():
        return ResolutionReport()
    data = json.loads(path.read_text())
    entries = [
        ResolutionEntry(
            table=r["table"],
            column=r.get("column"),
            reason=r["reason"],
            resolved_at=r["resolved_at"],
            resolved_by=r.get("resolved_by", "unknown"),
        )
        for r in data.get("entries", [])
    ]
    return ResolutionReport(entries=entries)


def save_resolutions(profile: str, report: ResolutionReport) -> None:
    path = _resolution_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "entries": [
            {
                "table": e.table,
                "column": e.column,
                "reason": e.reason,
                "resolved_at": e.resolved_at,
                "resolved_by": e.resolved_by,
            }
            for e in report.entries
        ]
    }
    path.write_text(json.dumps(data, indent=2))


def add_resolution(
    profile: str,
    table: str,
    reason: str,
    column: Optional[str] = None,
    resolved_by: str = "unknown",
) -> ResolutionEntry:
    report = load_resolutions(profile)
    entry = ResolutionEntry(
        table=table, column=column, reason=reason, resolved_by=resolved_by
    )
    report.entries = [e for e in report.entries if e.key() != entry.key()]
    report.entries.append(entry)
    save_resolutions(profile, report)
    return entry


def remove_resolution(
    profile: str, table: str, column: Optional[str] = None
) -> bool:
    report = load_resolutions(profile)
    key = f"{table}.{column}" if column else table
    before = len(report.entries)
    report.entries = [e for e in report.entries if e.key() != key]
    if len(report.entries) < before:
        save_resolutions(profile, report)
        return True
    return False
