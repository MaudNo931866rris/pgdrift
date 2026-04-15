"""Trend analysis: compare a series of historical snapshots to detect drift patterns."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pgdrift.history import list_history, load_history
from pgdrift.diff import compute_drift, DriftReport


@dataclass
class TrendPoint:
    captured_at: str
    profile: str
    added_tables: int
    removed_tables: int
    modified_tables: int
    total_changes: int


@dataclass
class TrendReport:
    profile: str
    points: List[TrendPoint] = field(default_factory=list)

    def is_stable(self) -> bool:
        """Return True if no drift was detected across all snapshots."""
        return all(p.total_changes == 0 for p in self.points)

    def peak(self) -> Optional[TrendPoint]:
        """Return the snapshot with the most total changes."""
        if not self.points:
            return None
        return max(self.points, key=lambda p: p.total_changes)


def _point_from_report(report: DriftReport, captured_at: str, profile: str) -> TrendPoint:
    added = len(report.added_tables)
    removed = len(report.removed_tables)
    modified = len(report.modified_tables)
    return TrendPoint(
        captured_at=captured_at,
        profile=profile,
        added_tables=added,
        removed_tables=removed,
        modified_tables=modified,
        total_changes=added + removed + modified,
    )


def build_trend(profile: str, limit: int = 10) -> TrendReport:
    """Load the most recent *limit* history entries for *profile* and build a TrendReport."""
    entries = list_history(profile)
    entries = entries[-limit:]

    points: List[TrendPoint] = []
    prev_tables = None

    for entry in entries:
        snapshot = load_history(entry["file"])
        if snapshot is None:
            continue
        current_tables = snapshot.get("tables", {})
        if prev_tables is not None:
            report = compute_drift(
                source_tables=prev_tables,
                target_tables=current_tables,
                source_name=profile,
                target_name=profile,
            )
            points.append(_point_from_report(report, entry.get("captured_at", ""), profile))
        prev_tables = current_tables

    return TrendReport(profile=profile, points=points)
