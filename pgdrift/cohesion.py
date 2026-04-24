"""Cohesion analysis: measures how tightly related columns within a table are
based on naming conventions and type consistency."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pgdrift.inspector import TableSchema


@dataclass
class CohesionEntry:
    table: str
    column_count: int
    type_variety: int          # distinct data types used
    prefix_groups: int         # distinct name-prefix groups
    score: float               # 0.0 (low) – 1.0 (high)

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "column_count": self.column_count,
            "type_variety": self.type_variety,
            "prefix_groups": self.prefix_groups,
            "score": round(self.score, 4),
        }


@dataclass
class CohesionReport:
    entries: List[CohesionEntry] = field(default_factory=list)

    def least_cohesive(self, n: int = 5) -> List[CohesionEntry]:
        return sorted(self.entries, key=lambda e: e.score)[:n]

    def average_score(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.score for e in self.entries) / len(self.entries)

    def as_dict(self) -> dict:
        return {
            "average_score": round(self.average_score(), 4),
            "entries": [e.as_dict() for e in self.entries],
        }


def _prefix_groups(names: List[str]) -> int:
    """Count distinct single-word prefixes (split on '_')."""
    if not names:
        return 0
    prefixes = {n.split("_")[0] for n in names}
    return len(prefixes)


def _cohesion_score(type_variety: int, prefix_groups: int, column_count: int) -> float:
    """Higher variety and more prefix groups → lower cohesion."""
    if column_count == 0:
        return 1.0
    type_penalty = min(1.0, (type_variety - 1) / max(column_count, 1))
    prefix_penalty = min(1.0, (prefix_groups - 1) / max(column_count, 1))
    raw = 1.0 - (type_penalty * 0.5 + prefix_penalty * 0.5)
    return max(0.0, min(1.0, raw))


def compute_cohesion(tables: Dict[str, TableSchema]) -> CohesionReport:
    entries: List[CohesionEntry] = []
    for full_name, schema in tables.items():
        cols = list(schema.columns.values())
        col_count = len(cols)
        type_variety = len({c.data_type for c in cols}) if cols else 0
        pg = _prefix_groups([c.name for c in cols])
        score = _cohesion_score(type_variety, pg, col_count)
        entries.append(
            CohesionEntry(
                table=full_name,
                column_count=col_count,
                type_variety=type_variety,
                prefix_groups=pg,
                score=score,
            )
        )
    return CohesionReport(entries=entries)
