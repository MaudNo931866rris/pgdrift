"""Freshness check: report how recently each snapshot was captured."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_SNAPSHOT_DIR = Path(".pgdrift") / "snapshots"


@dataclass
class FreshnessEntry:
    profile: str
    snapshot_file: str
    captured_at: datetime
    age_hours: float
    is_fresh: bool


@dataclass
class FreshnessReport:
    entries: List[FreshnessEntry]

    def stale_entries(self) -> List[FreshnessEntry]:
        return [e for e in self.entries if not e.is_fresh]

    def any_stale(self) -> bool:
        return any(not e.is_fresh for e in self.entries)


def _parse_captured_at(raw: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def compute_freshness(
    snapshot_dir: Path = _SNAPSHOT_DIR,
    max_age_hours: float = 24.0,
    now: Optional[datetime] = None,
) -> FreshnessReport:
    if now is None:
        now = datetime.now(timezone.utc)

    entries: List[FreshnessEntry] = []

    if not snapshot_dir.exists():
        return FreshnessReport(entries=[])

    for path in sorted(snapshot_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        raw_ts = data.get("captured_at")
        captured_at = _parse_captured_at(raw_ts) if raw_ts else None
        if captured_at is None:
            continue

        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)

        delta = now - captured_at
        age_hours = delta.total_seconds() / 3600
        profile = data.get("profile", path.stem)

        entries.append(
            FreshnessEntry(
                profile=profile,
                snapshot_file=path.name,
                captured_at=captured_at,
                age_hours=round(age_hours, 2),
                is_fresh=age_hours <= max_age_hours,
            )
        )

    return FreshnessReport(entries=entries)
