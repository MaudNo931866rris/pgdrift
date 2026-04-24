"""Schema density analysis — measures how 'filled out' tables are
based on nullable vs non-nullable columns and overall column counts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.inspector import TableSchema


@dataclass
class DensityEntry:
    table: str
    total_columns: int
    non_nullable_columns: int
    nullable_columns: int
    density_score: float  # 0.0 – 1.0

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "total_columns": self.total_columns,
            "non_nullable_columns": self.non_nullable_columns,
            "nullable_columns": self.nullable_columns,
            "density_score": round(self.density_score, 4),
        }


@dataclass
class DensityReport:
    entries: List[DensityEntry] = field(default_factory=list)

    def average_score(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.density_score for e in self.entries) / len(self.entries)

    def least_dense(self, n: int = 5) -> List[DensityEntry]:
        return sorted(self.entries, key=lambda e: e.density_score)[:n]

    def most_dense(self, n: int = 5) -> List[DensityEntry]:
        return sorted(self.entries, key=lambda e: e.density_score, reverse=True)[:n]

    def as_dict(self) -> dict:
        return {
            "average_score": round(self.average_score(), 4),
            "entries": [e.as_dict() for e in self.entries],
        }


def _density_score(total: int, non_nullable: int) -> float:
    """Fraction of columns that are non-nullable (strict / required)."""
    if total == 0:
        return 0.0
    return non_nullable / total


def compute_density(tables: List[TableSchema]) -> DensityReport:
    entries: List[DensityEntry] = []
    for table in tables:
        total = len(table.columns)
        non_nullable = sum(1 for c in table.columns if not c.nullable)
        nullable = total - non_nullable
        score = _density_score(total, non_nullable)
        entries.append(
            DensityEntry(
                table=table.full_name(),
                total_columns=total,
                non_nullable_columns=non_nullable,
                nullable_columns=nullable,
                density_score=score,
            )
        )
    return DensityReport(entries=entries)
