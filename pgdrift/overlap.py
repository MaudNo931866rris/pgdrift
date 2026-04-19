"""Detect column name overlap between two schemas."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from pgdrift.inspector import TableSchema


@dataclass
class OverlapEntry:
    table: str
    shared_columns: List[str]
    source_only: List[str]
    target_only: List[str]

    def overlap_ratio(self) -> float:
        total = len(self.shared_columns) + len(self.source_only) + len(self.target_only)
        if total == 0:
            return 1.0
        return len(self.shared_columns) / total

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "shared_columns": self.shared_columns,
            "source_only": self.source_only,
            "target_only": self.target_only,
            "overlap_ratio": round(self.overlap_ratio(), 4),
        }


@dataclass
class OverlapReport:
    entries: List[OverlapEntry] = field(default_factory=list)

    def any_divergence(self) -> bool:
        return any(e.source_only or e.target_only for e in self.entries)

    def as_dict(self) -> dict:
        return {
            "entries": [e.as_dict() for e in self.entries],
            "any_divergence": self.any_divergence(),
        }


def compute_overlap(
    source: Dict[str, TableSchema],
    target: Dict[str, TableSchema],
) -> OverlapReport:
    entries: List[OverlapEntry] = []
    common_tables = set(source.keys()) & set(target.keys())
    for name in sorted(common_tables):
        src_cols = {c.name for c in source[name].columns}
        tgt_cols = {c.name for c in target[name].columns}
        entries.append(
            OverlapEntry(
                table=name,
                shared_columns=sorted(src_cols & tgt_cols),
                source_only=sorted(src_cols - tgt_cols),
                target_only=sorted(tgt_cols - src_cols),
            )
        )
    return OverlapReport(entries=entries)
