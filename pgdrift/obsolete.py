"""Detect obsolete columns: columns present in source but absent in target for a long time."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pgdrift.diff import DriftReport, TableDiff


@dataclass
class ObsoleteColumn:
    schema: str
    table: str
    column: str
    data_type: str

    def as_dict(self) -> dict:
        return {
            "schema": self.schema,
            "table": self.table,
            "column": self.column,
            "data_type": self.data_type,
        }


@dataclass
class ObsoleteReport:
    entries: List[ObsoleteColumn] = field(default_factory=list)

    def any_obsolete(self) -> bool:
        return len(self.entries) > 0

    def by_table(self, schema: str, table: str) -> List[ObsoleteColumn]:
        return [e for e in self.entries if e.schema == schema and e.table == table]

    def as_dict(self) -> dict:
        return {"entries": [e.as_dict() for e in self.entries]}


def compute_obsolete(report: DriftReport) -> ObsoleteReport:
    """Return columns removed in target (present in source, missing in target)."""
    entries: List[ObsoleteColumn] = []
    for td in report.tables:
        for cd in td.columns:
            if cd.status == "removed":
                entries.append(
                    ObsoleteColumn(
                        schema=td.schema,
                        table=td.table,
                        column=cd.column,
                        data_type=cd.source_type or "",
                    )
                )
    return ObsoleteReport(entries=entries)
