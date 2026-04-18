"""Detect likely column/table renames between two schemas using name similarity."""
from __future__ import annotations
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List

from pgdrift.diff import DriftReport, TableDiff


@dataclass
class RenameCandidate:
    kind: str  # 'table' or 'column'
    table: str
    old_name: str
    new_name: str
    score: float

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "table": self.table,
            "old_name": self.old_name,
            "new_name": self.new_name,
            "score": round(self.score, 3),
        }


@dataclass
class RenameReport:
    candidates: List[RenameCandidate] = field(default_factory=list)

    def has_candidates(self) -> bool:
        return len(self.candidates) > 0

    def as_dict(self) -> dict:
        return {"candidates": [c.as_dict() for c in self.candidates]}


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _best_match(name: str, pool: List[str], threshold: float) -> tuple[str, float] | None:
    best, best_score = None, 0.0
    for candidate in pool:
        s = _similarity(name, candidate)
        if s > best_score:
            best, best_score = candidate, s
    if best and best_score >= threshold:
        return best, best_score
    return None


def detect_renames(report: DriftReport, threshold: float = 0.6) -> RenameReport:
    """Heuristically detect renames from added/removed tables and columns."""
    result = RenameReport()

    removed_tables = [t.table_name for t in report.tables if t.removed]
    added_tables = [t.table_name for t in report.tables if t.added]

    matched_removed: set[str] = set()
    for added in added_tables:
        match = _best_match(added, removed_tables, threshold)
        if match:
            old_name, score = match
            if old_name not in matched_removed:
                matched_removed.add(old_name)
                result.candidates.append(
                    RenameCandidate("table", "", old_name, added, score)
                )

    for td in report.tables:
        if td.added or td.removed:
            continue
        removed_cols = [c.column_name for c in td.column_diffs if c.removed]
        added_cols = [c.column_name for c in td.column_diffs if c.added]
        matched: set[str] = set()
        for ac in added_cols:
            match = _best_match(ac, removed_cols, threshold)
            if match:
                old_col, score = match
                if old_col not in matched:
                    matched.add(old_col)
                    result.candidates.append(
                        RenameCandidate("column", td.table_name, old_col, ac, score)
                    )

    return result
