"""Track and report deprecated column/table usage across schema snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


def _deprecation_path(base_dir: str = ".pgdrift") -> Path:
    return Path(base_dir) / "deprecations.json"


@dataclass
class DeprecationEntry:
    schema: str
    table: str
    column: Optional[str]  # None means the whole table is deprecated
    reason: str
    since: str  # ISO date string

    def key(self) -> str:
        if self.column:
            return f"{self.schema}.{self.table}.{self.column}"
        return f"{self.schema}.{self.table}"


@dataclass
class DeprecationReport:
    entries: List[DeprecationEntry] = field(default_factory=list)

    def by_table(self, schema: str, table: str) -> List[DeprecationEntry]:
        return [e for e in self.entries if e.schema == schema and e.table == table]

    def is_deprecated(self, schema: str, table: str, column: Optional[str] = None) -> bool:
        for e in self.entries:
            if e.schema == schema and e.table == table:
                if column is None or e.column is None or e.column == column:
                    return True
        return False


def load_deprecations(base_dir: str = ".pgdrift") -> DeprecationReport:
    path = _deprecation_path(base_dir)
    if not path.exists():
        return DeprecationReport()
    data = json.loads(path.read_text())
    entries = [DeprecationEntry(**e) for e in data.get("entries", [])]
    return DeprecationReport(entries=entries)


def save_deprecations(report: DeprecationReport, base_dir: str = ".pgdrift") -> None:
    path = _deprecation_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"entries": [asdict(e) for e in report.entries]}
    path.write_text(json.dumps(payload, indent=2))


def add_deprecation(entry: DeprecationEntry, base_dir: str = ".pgdrift") -> None:
    report = load_deprecations(base_dir)
    report.entries = [e for e in report.entries if e.key() != entry.key()]
    report.entries.append(entry)
    save_deprecations(report, base_dir)


def remove_deprecation(key: str, base_dir: str = ".pgdrift") -> bool:
    report = load_deprecations(base_dir)
    before = len(report.entries)
    report.entries = [e for e in report.entries if e.key() != key]
    if len(report.entries) < before:
        save_deprecations(report, base_dir)
        return True
    return False
