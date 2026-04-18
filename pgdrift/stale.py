"""Detect stale snapshots based on age thresholds."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class StaleEntry:
    profile: str
    snapshot_file: str
    captured_at: datetime
    age_days: float
    is_stale: bool


@dataclass
class StaleReport:
    entries: List[StaleEntry] = field(default_factory=list)
    max_age_days: float = 7.0

    def stale_entries(self) -> List[StaleEntry]:
        return [e for e in self.entries if e.is_stale]

    def any_stale(self) -> bool:
        return any(e.is_stale for e in self.entries)


def _parse_captured_at(raw: str) -> datetime:
    return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)


def check_stale(snapshot_dir: Path, max_age_days: float = 7.0) -> StaleReport:
    """Scan snapshot_dir for JSON snapshots and flag stale ones."""
    report = StaleReport(max_age_days=max_age_days)
    now = datetime.now(tz=timezone.utc)

    if not snapshot_dir.exists():
        return report

    for path in sorted(snapshot_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        captured_raw = data.get("captured_at")
        profile = data.get("profile", path.stem)
        if not captured_raw:
            continue

        captured_at = _parse_captured_at(captured_raw)
        age = (now - captured_at).total_seconds() / 86400.0
        entry = StaleEntry(
            profile=profile,
            snapshot_file=path.name,
            captured_at=captured_at,
            age_days=round(age, 2),
            is_stale=age > max_age_days,
        )
        report.entries.append(entry)

    return report
