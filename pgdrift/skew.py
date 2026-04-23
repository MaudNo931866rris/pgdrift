"""Skew detection: identify tables whose column counts deviate significantly
from the mean across all tables in a schema snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.inspector import TableSchema


@dataclass
class SkewEntry:
    table: str
    column_count: int
    deviation: float  # distance from mean in column counts


def as_dict(entry: SkewEntry) -> dict:
    return {
        "table": entry.table,
        "column_count": entry.column_count,
        "deviation": round(entry.deviation, 4),
    }


@dataclass
class SkewReport:
    entries: List[SkewEntry] = field(default_factory=list)
    mean_columns: float = 0.0
    stddev: float = 0.0

    def any_skew(self, threshold: float = 2.0) -> bool:
        """Return True if any table deviates more than *threshold* standard deviations."""
        return any(abs(e.deviation) > threshold for e in self.entries)

    def outliers(self, threshold: float = 2.0) -> List[SkewEntry]:
        return [e for e in self.entries if abs(e.deviation) > threshold]


def compute_skew(tables: List[TableSchema]) -> SkewReport:
    """Compute column-count skew across *tables*."""
    if not tables:
        return SkewReport()

    counts = [len(t.columns) for t in tables]
    mean = sum(counts) / len(counts)

    variance = sum((c - mean) ** 2 for c in counts) / len(counts)
    stddev = variance ** 0.5

    entries: List[SkewEntry] = []
    for table, count in zip(tables, counts):
        deviation = (count - mean) / stddev if stddev > 0 else 0.0
        entries.append(
            SkewEntry(
                table=table.full_name,
                column_count=count,
                deviation=deviation,
            )
        )

    entries.sort(key=lambda e: abs(e.deviation), reverse=True)
    return SkewReport(entries=entries, mean_columns=round(mean, 4), stddev=round(stddev, 4))
