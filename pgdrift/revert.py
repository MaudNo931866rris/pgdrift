"""Revert suggestions: given a DriftReport, produce SQL stubs to undo drift."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from pgdrift.diff import DriftReport, TableDiff


@dataclass
class RevertStatement:
    table: str
    sql: str
    reason: str


@dataclass
class RevertPlan:
    statements: List[RevertStatement] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.statements) == 0


def _revert_table_diff(td: TableDiff) -> List[RevertStatement]:
    stmts: List[RevertStatement] = []
    if td.status == "added":
        stmts.append(RevertStatement(
            table=td.table,
            sql=f"DROP TABLE IF EXISTS {td.table};",
            reason="Table was added in target; drop to revert.",
        ))
    elif td.status == "removed":
        stmts.append(RevertStatement(
            table=td.table,
            sql=f"-- Recreate table {td.table} from source schema (manual);",
            reason="Table was removed in target; manual recreation required.",
        ))
    else:
        for cd in td.column_diffs:
            if cd.status == "added":
                stmts.append(RevertStatement(
                    table=td.table,
                    sql=f"ALTER TABLE {td.table} DROP COLUMN IF EXISTS {cd.column};",
                    reason=f"Column '{cd.column}' was added in target.",
                ))
            elif cd.status == "removed":
                src = cd.source
                null = "" if src and src.nullable else " NOT NULL"
                dtype = src.data_type if src else "text"
                stmts.append(RevertStatement(
                    table=td.table,
                    sql=f"ALTER TABLE {td.table} ADD COLUMN {cd.column} {dtype}{null};",
                    reason=f"Column '{cd.column}' was removed in target.",
                ))
            elif cd.status == "modified":
                src = cd.source
                if src:
                    stmts.append(RevertStatement(
                        table=td.table,
                        sql=f"ALTER TABLE {td.table} ALTER COLUMN {cd.column} TYPE {src.data_type};",
                        reason=f"Column '{cd.column}' type changed; reverting to source type.",
                    ))
    return stmts


def build_revert_plan(report: DriftReport) -> RevertPlan:
    plan = RevertPlan()
    for td in report.table_diffs:
        plan.statements.extend(_revert_table_diff(td))
    return plan
