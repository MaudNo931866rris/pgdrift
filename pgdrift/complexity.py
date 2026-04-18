from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from pgdrift.inspector import TableSchema


@dataclass
class TableComplexity:
    full_name: str
    column_count: int
    nullable_count: int
    type_variety: int
    score: float

    def as_dict(self) -> dict:
        return {
            "table": self.full_name,
            "column_count": self.column_count,
            "nullable_count": self.nullable_count,
            "type_variety": self.type_variety,
            "score": round(self.score, 3),
        }


@dataclass
class ComplexityReport:
    entries: List[TableComplexity] = field(default_factory=list)

    def most_complex(self) -> TableComplexity | None:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.score)

    def average_score(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.score for e in self.entries) / len(self.entries)

    def as_dict(self) -> dict:
        return {
            "average_score": round(self.average_score(), 3),
            "tables": [e.as_dict() for e in self.entries],
        }


def _score(table: TableSchema) -> float:
    cols = table.columns
    if not cols:
        return 0.0
    nullable_ratio = sum(1 for c in cols if c.nullable) / len(cols)
    types = len({c.data_type for c in cols})
    type_ratio = min(types / max(len(cols), 1), 1.0)
    return round(len(cols) * 0.5 + nullable_ratio * 2.0 + type_ratio * 1.5, 3)


def compute_complexity(tables: List[TableSchema]) -> ComplexityReport:
    entries = []
    for t in tables:
        cols = t.columns
        nullable = sum(1 for c in cols if c.nullable)
        types = len({c.data_type for c in cols})
        entries.append(TableComplexity(
            full_name=t.full_name,
            column_count=len(cols),
            nullable_count=nullable,
            type_variety=types,
            score=_score(t),
        ))
    return ComplexityReport(entries=entries)
