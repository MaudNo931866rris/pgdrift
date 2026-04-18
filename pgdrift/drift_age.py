"""Drift age: track how long drift has been present across audit entries."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from pgdrift.audit import load_audit


@dataclass
class DriftAgeEntry:
    table: str
    first_seen: datetime
    last_seen: datetime
    occurrences: int

    @property
    def age_days(self) -> float:
        now = datetime.now(timezone.utc)
        first = self.first_seen.replace(tzinfo=timezone.utc) if self.first_seen.tzinfo is None else self.first_seen
        return (now - first).total_seconds() / 86400


@dataclass
class DriftAgeReport:
    entries: List[DriftAgeEntry]

    def oldest(self) -> Optional[DriftAgeEntry]:
        return min(self.entries, key=lambda e: e.first_seen, default=None)

    def as_dict(self) -> dict:
        return {
            "entries": [
                {
                    "table": e.table,
                    "first_seen": e.first_seen.isoformat(),
                    "last_seen": e.last_seen.isoformat(),
                    "occurrences": e.occurrences,
                    "age_days": round(e.age_days, 2),
                }
                for e in self.entries
            ]
        }


def compute_drift_age(profile: str, audit_dir: Optional[str] = None) -> DriftAgeReport:
    """Scan audit history for a profile and compute per-table drift age."""
    entries = load_audit(profile, audit_dir=audit_dir)
    table_data: dict = {}

    for entry in entries:
        ts_raw = entry.get("captured_at", "")
        try:
            ts = datetime.fromisoformat(ts_raw)
        except (ValueError, TypeError):
            continue

        report = entry.get("report", {})
        added = [t["table"] for t in report.get("added_tables", [])]
        removed = [t["table"] for t in report.get("removed_tables", [])]
        modified = [t["table"] for t in report.get("modified_tables", [])]

        for table in set(added + removed + modified):
            if table not in table_data:
                table_data[table] = {"first_seen": ts, "last_seen": ts, "occurrences": 0}
            else:
                if ts < table_data[table]["first_seen"]:
                    table_data[table]["first_seen"] = ts
                if ts > table_data[table]["last_seen"]:
                    table_data[table]["last_seen"] = ts
            table_data[table]["occurrences"] += 1

    result = [
        DriftAgeEntry(
            table=table,
            first_seen=data["first_seen"],
            last_seen=data["last_seen"],
            occurrences=data["occurrences"],
        )
        for table, data in table_data.items()
    ]
    result.sort(key=lambda e: e.first_seen)
    return DriftAgeReport(entries=result)
