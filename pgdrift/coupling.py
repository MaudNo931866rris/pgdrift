"""Detect co-changing tables (coupling) from audit history."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List, Tuple
from pgdrift.audit import load_audit


@dataclass
class CouplingPair:
    table_a: str
    table_b: str
    co_changes: int
    total_snapshots: int

    def coupling_ratio(self) -> float:
        if self.total_snapshots == 0:
            return 0.0
        return round(self.co_changes / self.total_snapshots, 4)

    def as_dict(self) -> dict:
        return {
            "table_a": self.table_a,
            "table_b": self.table_b,
            "co_changes": self.co_changes,
            "total_snapshots": self.total_snapshots,
            "coupling_ratio": self.coupling_ratio(),
        }


@dataclass
class CouplingReport:
    pairs: List[CouplingPair] = field(default_factory=list)

    def has_coupling(self) -> bool:
        return bool(self.pairs)

    def strong_pairs(self, threshold: float = 0.5) -> List[CouplingPair]:
        return [p for p in self.pairs if p.coupling_ratio() >= threshold]


def compute_coupling(audit_dir: str, min_co_changes: int = 2) -> CouplingReport:
    entries = load_audit(audit_dir)
    if not entries:
        return CouplingReport()

    snapshots: List[set] = []
    for entry in entries:
        changed = set()
        for td in entry.get("report", {}).get("tables", []):
            changed.add(td.get("table", ""))
        if changed:
            snapshots.append(changed)

    total = len(snapshots)
    counts: Dict[Tuple[str, str], int] = defaultdict(int)

    for changed in snapshots:
        tables = sorted(changed)
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                counts[(tables[i], tables[j])] += 1

    pairs = [
        CouplingPair(a, b, c, total)
        for (a, b), c in counts.items()
        if c >= min_co_changes
    ]
    pairs.sort(key=lambda p: p.coupling_ratio(), reverse=True)
    return CouplingReport(pairs=pairs)
