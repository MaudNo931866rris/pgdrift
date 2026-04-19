"""Detect schema bloat: tables with too many columns or excessive nullable columns."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pgdrift.inspector import TableSchema

DEFAULT_MAX_COLUMNS = 30
DEFAULT_MAX_NULLABLE_RATIO = 0.6


@dataclass
class BloatEntry:
    table: str
    column_count: int
    nullable_count: int
    nullable_ratio: float
    reasons: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "column_count": self.column_count,
            "nullable_count": self.nullable_count,
            "nullable_ratio": round(self.nullable_ratio, 3),
            "reasons": self.reasons,
        }


@dataclass
class BloatReport:
    entries: List[BloatEntry] = field(default_factory=list)

    def any_bloat(self) -> bool:
        return len(self.entries) > 0

    def most_bloated(self, n: int = 5) -> List[BloatEntry]:
        return sorted(self.entries, key=lambda e: e.column_count, reverse=True)[:n]

    def as_dict(self) -> dict:
        return {"entries": [e.as_dict() for e in self.entries]}


def compute_bloat(
    tables: List[TableSchema],
    max_columns: int = DEFAULT_MAX_COLUMNS,
    max_nullable_ratio: float = DEFAULT_MAX_NULLABLE_RATIO,
) -> BloatReport:
    entries: List[BloatEntry] = []
    for t in tables:
        reasons: List[str] = []
        col_count = len(t.columns)
        nullable_count = sum(1 for c in t.columns if c.nullable)
        ratio = nullable_count / col_count if col_count else 0.0

        if col_count > max_columns:
            reasons.append(f"column count {col_count} exceeds limit {max_columns}")
        if col_count > 0 and ratio > max_nullable_ratio:
            reasons.append(
                f"nullable ratio {ratio:.2f} exceeds limit {max_nullable_ratio}"
            )
        if reasons:
            entries.append(
                BloatEntry(
                    table=t.full_name(),
                    column_count=col_count,
                    nullable_count=nullable_count,
                    nullable_ratio=ratio,
                    reasons=reasons,
                )
            )
    return BloatReport(entries=entries)
