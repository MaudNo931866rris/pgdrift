"""Conformance checking: measure how well a schema adheres to naming/type conventions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from pgdrift.inspector import TableSchema


@dataclass
class ConformanceViolation:
    table: str
    column: str
    rule: str
    detail: str

    def as_dict(self) -> Dict:
        return {
            "table": self.table,
            "column": self.column,
            "rule": self.rule,
            "detail": self.detail,
        }


@dataclass
class ConformanceReport:
    violations: List[ConformanceViolation] = field(default_factory=list)

    @property
    def any_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def as_dict(self) -> Dict:
        return {
            "violation_count": self.violation_count,
            "any_violations": self.any_violations,
            "violations": [v.as_dict() for v in self.violations],
        }


_SNAKE_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_")


def _is_snake_case(name: str) -> bool:
    return bool(name) and all(c in _SNAKE_CHARS for c in name) and not name.startswith("_")


_PREFERRED_ID_TYPES = {"integer", "bigint", "uuid"}


def compute_conformance(tables: List[TableSchema]) -> ConformanceReport:
    """Check tables and columns against common naming and type conventions."""
    violations: List[ConformanceViolation] = []

    for table in tables:
        if not _is_snake_case(table.name):
            violations.append(
                ConformanceViolation(
                    table=table.name,
                    column="",
                    rule="snake_case_table",
                    detail=f"Table name '{table.name}' is not snake_case",
                )
            )

        for col in table.columns:
            if not _is_snake_case(col.name):
                violations.append(
                    ConformanceViolation(
                        table=table.name,
                        column=col.name,
                        rule="snake_case_column",
                        detail=f"Column name '{col.name}' is not snake_case",
                    )
                )

            if col.name == "id" and col.data_type.lower() not in _PREFERRED_ID_TYPES:
                violations.append(
                    ConformanceViolation(
                        table=table.name,
                        column=col.name,
                        rule="id_column_type",
                        detail=(
                            f"Primary key 'id' has type '{col.data_type}'; "
                            f"expected one of {sorted(_PREFERRED_ID_TYPES)}"
                        ),
                    )
                )

    return ConformanceReport(violations=violations)
