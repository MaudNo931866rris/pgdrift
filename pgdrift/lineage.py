"""Track column lineage — record which columns have been added, removed, or
renamed across captured snapshots so callers can trace a column's history."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


def _lineage_path(base_dir: str = ".pgdrift") -> Path:
    p = Path(base_dir) / "lineage"
    p.mkdir(parents=True, exist_ok=True)
    return p


@dataclass
class LineageEvent:
    event: str          # "added" | "removed" | "renamed"
    table: str
    column: str
    snapshot: str       # snapshot filename / label
    captured_at: str
    detail: Optional[str] = None   # e.g. old name for renames


@dataclass
class LineageReport:
    events: List[LineageEvent] = field(default_factory=list)

    def for_table(self, table: str) -> List[LineageEvent]:
        return [e for e in self.events if e.table == table]

    def for_column(self, table: str, column: str) -> List[LineageEvent]:
        return [e for e in self.events if e.table == table and e.column == column]

    def as_dict(self) -> Dict:
        return {"events": [asdict(e) for e in self.events]}


def save_lineage(report: LineageReport, label: str, base_dir: str = ".pgdrift") -> Path:
    path = _lineage_path(base_dir) / f"{label}.json"
    path.write_text(json.dumps(report.as_dict(), indent=2))
    return path


def load_lineage(label: str, base_dir: str = ".pgdrift") -> Optional[LineageReport]:
    path = _lineage_path(base_dir) / f"{label}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    events = [LineageEvent(**e) for e in data.get("events", [])]
    return LineageReport(events=events)


def list_lineage(base_dir: str = ".pgdrift") -> List[str]:
    return sorted(p.stem for p in _lineage_path(base_dir).glob("*.json"))


def build_lineage(diff_report, snapshot_label: str, captured_at: str) -> LineageReport:
    """Derive a LineageReport from a DriftReport."""
    events: List[LineageEvent] = []
    for td in diff_report.table_diffs:
        for col in td.added_columns:
            events.append(LineageEvent("added", td.table_name, col.column_name, snapshot_label, captured_at))
        for col in td.removed_columns:
            events.append(LineageEvent("removed", td.table_name, col.column_name, snapshot_label, captured_at))
        for cd in td.modified_columns:
            events.append(LineageEvent("modified", td.table_name, cd.column_name, snapshot_label, captured_at))
    return LineageReport(events=events)
