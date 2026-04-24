"""Symmetry analysis: measures how structurally symmetric two schemas are.

A symmetric schema pair has the same tables and columns in both directions.
The symmetry score is 1.0 when schemas are identical, 0.0 when completely disjoint.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from pgdrift.inspector import TableSchema


@dataclass
class SymmetryEntry:
    table: str
    source_columns: int
    target_columns: int
    common_columns: int
    score: float  # 0.0 – 1.0


def as_dict(entry: SymmetryEntry) -> dict:
    return {
        "table": entry.table,
        "source_columns": entry.source_columns,
        "target_columns": entry.target_columns,
        "common_columns": entry.common_columns,
        "score": round(entry.score, 4),
    }


@dataclass
class SymmetryReport:
    entries: List[SymmetryEntry] = field(default_factory=list)
    table_symmetry: float = 0.0  # ratio of shared tables to union of tables


def overall_score(report: SymmetryReport) -> float:
    """Mean column-level symmetry score across all shared tables."""
    if not report.entries:
        return report.table_symmetry
    col_mean = sum(e.score for e in report.entries) / len(report.entries)
    return round((col_mean + report.table_symmetry) / 2, 4)


def _column_symmetry(source: TableSchema, target: TableSchema) -> SymmetryEntry:
    src_cols = {c.name for c in source.columns}
    tgt_cols = {c.name for c in target.columns}
    common = src_cols & tgt_cols
    union = src_cols | tgt_cols
    score = len(common) / len(union) if union else 1.0
    return SymmetryEntry(
        table=source.name,
        source_columns=len(src_cols),
        target_columns=len(tgt_cols),
        common_columns=len(common),
        score=score,
    )


def compute_symmetry(
    source_tables: List[TableSchema],
    target_tables: List[TableSchema],
) -> SymmetryReport:
    src_map: Dict[str, TableSchema] = {t.name: t for t in source_tables}
    tgt_map: Dict[str, TableSchema] = {t.name: t for t in target_tables}

    src_names = set(src_map)
    tgt_names = set(tgt_map)
    shared = src_names & tgt_names
    union = src_names | tgt_names

    table_sym = len(shared) / len(union) if union else 1.0

    entries = [
        _column_symmetry(src_map[name], tgt_map[name])
        for name in sorted(shared)
    ]

    return SymmetryReport(entries=entries, table_symmetry=round(table_sym, 4))
