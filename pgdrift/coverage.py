"""Schema coverage: measure how much of the target schema is present in the source."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from pgdrift.inspector import TableSchema


@dataclass
class TableCoverage:
    table: str
    source_columns: int
    target_columns: int
    matched_columns: int

    @property
    def ratio(self) -> float:
        if self.target_columns == 0:
            return 1.0
        return self.matched_columns / self.target_columns

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "source_columns": self.source_columns,
            "target_columns": self.target_columns,
            "matched_columns": self.matched_columns,
            "ratio": round(self.ratio, 4),
        }


@dataclass
class CoverageReport:
    tables: List[TableCoverage] = field(default_factory=list)

    @property
    def overall_ratio(self) -> float:
        if not self.tables:
            return 1.0
        return sum(t.ratio for t in self.tables) / len(self.tables)

    @property
    def missing_tables(self) -> List[str]:
        return [t.table for t in self.tables if t.source_columns == 0]

    def as_dict(self) -> dict:
        return {
            "overall_ratio": round(self.overall_ratio, 4),
            "missing_tables": self.missing_tables,
            "tables": [t.as_dict() for t in self.tables],
        }


def compute_coverage(
    source: Dict[str, TableSchema],
    target: Dict[str, TableSchema],
) -> CoverageReport:
    entries: List[TableCoverage] = []
    for name, tgt_table in target.items():
        src_table = source.get(name)
        src_cols = set(src_table.columns.keys()) if src_table else set()
        tgt_cols = set(tgt_table.columns.keys())
        entries.append(
            TableCoverage(
                table=name,
                source_columns=len(src_cols),
                target_columns=len(tgt_cols),
                matched_columns=len(src_cols & tgt_cols),
            )
        )
    return CoverageReport(tables=entries)
