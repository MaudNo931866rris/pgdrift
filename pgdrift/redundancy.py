"""Detect redundant columns: columns that share identical name patterns and types across many tables."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List

from pgdrift.inspector import TableSchema


@dataclass
class RedundancyEntry:
    column_name: str
    data_type: str
    tables: List[str]
    occurrence_count: int

    def as_dict(self) -> dict:
        return {
            "column_name": self.column_name,
            "data_type": self.data_type,
            "tables": self.tables,
            "occurrence_count": self.occurrence_count,
        }


@dataclass
class RedundancyReport:
    entries: List[RedundancyEntry] = field(default_factory=list)

    def any_redundant(self) -> bool:
        return len(self.entries) > 0

    def most_redundant(self, n: int = 5) -> List[RedundancyEntry]:
        return sorted(self.entries, key=lambda e: e.occurrence_count, reverse=True)[:n]

    def as_dict(self) -> dict:
        return {
            "entries": [e.as_dict() for e in self.entries],
            "total": len(self.entries),
        }


def compute_redundancy(
    tables: List[TableSchema],
    min_occurrences: int = 2,
) -> RedundancyReport:
    """Find column name+type pairs that appear in at least *min_occurrences* tables."""
    # key: (column_name, data_type) -> list of full table names
    index: Dict[tuple, List[str]] = defaultdict(list)

    for table in tables:
        full = f"{table.schema}.{table.name}"
        for col in table.columns:
            index[(col.name, col.data_type)].append(full)

    entries: List[RedundancyEntry] = []
    for (col_name, data_type), tbl_list in index.items():
        if len(tbl_list) >= min_occurrences:
            entries.append(
                RedundancyEntry(
                    column_name=col_name,
                    data_type=data_type,
                    tables=sorted(tbl_list),
                    occurrence_count=len(tbl_list),
                )
            )

    entries.sort(key=lambda e: e.occurrence_count, reverse=True)
    return RedundancyReport(entries=entries)
