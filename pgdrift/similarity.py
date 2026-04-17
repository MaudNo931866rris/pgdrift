"""Compute schema similarity scores between two sets of tables."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from pgdrift.inspector import TableSchema
from pgdrift.diff import DriftReport


@dataclass
class SimilarityResult:
    score: float          # 0.0 – 1.0
    matched: int
    total: int
    per_table: Dict[str, float]

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "matched": self.matched,
            "total": self.total,
            "per_table": {k: round(v, 4) for k, v in self.per_table.items()},
        }


def _table_similarity(a: TableSchema, b: TableSchema) -> float:
    """Column-level Jaccard similarity between two tables."""
    a_cols = {c.name for c in a.columns}
    b_cols = {c.name for c in b.columns}
    if not a_cols and not b_cols:
        return 1.0
    intersection = len(a_cols & b_cols)
    union = len(a_cols | b_cols)
    return intersection / union if union else 0.0


def compute_similarity(
    source: List[TableSchema],
    target: List[TableSchema],
) -> SimilarityResult:
    src_map = {t.full_name(): t for t in source}
    tgt_map = {t.full_name(): t for t in target}
    all_names = set(src_map) | set(tgt_map)
    per_table: Dict[str, float] = {}
    for name in all_names:
        if name in src_map and name in tgt_map:
            per_table[name] = _table_similarity(src_map[name], tgt_map[name])
        else:
            per_table[name] = 0.0
    total = len(all_names)
    matched = sum(1 for v in per_table.values() if v == 1.0)
    score = sum(per_table.values()) / total if total else 1.0
    return SimilarityResult(score=score, matched=matched, total=total, per_table=per_table)
