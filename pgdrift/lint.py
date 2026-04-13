"""Schema lint rules for detecting common schema issues."""

from dataclasses import dataclass, field
from typing import List
from pgdrift.inspector import TableSchema


@dataclass
class LintIssue:
    table: str
    column: str | None
    rule: str
    message: str
    severity: str = "warning"  # "warning" | "error"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def _check_missing_primary_key(table: TableSchema, issues: List[LintIssue]) -> None:
    column_names = [c.name.lower() for c in table.columns]
    if "id" not in column_names:
        issues.append(
            LintIssue(
                table=table.full_name,
                column=None,
                rule="missing_primary_key",
                message=f"Table '{table.full_name}' has no 'id' column.",
                severity="warning",
            )
        )


def _check_nullable_columns(table: TableSchema, issues: List[LintIssue]) -> None:
    for col in table.columns:
        if col.nullable and col.name.lower() in ("email", "username", "name"):
            issues.append(
                LintIssue(
                    table=table.full_name,
                    column=col.name,
                    rule="nullable_identity_column",
                    message=(
                        f"Column '{col.name}' in '{table.full_name}' "
                        "is nullable but appears to be an identity field."
                    ),
                    severity="warning",
                )
            )


def _check_generic_column_names(table: TableSchema, issues: List[LintIssue]) -> None:
    generic = {"data", "info", "value", "misc", "temp"}
    for col in table.columns:
        if col.name.lower() in generic:
            issues.append(
                LintIssue(
                    table=table.full_name,
                    column=col.name,
                    rule="generic_column_name",
                    message=(
                        f"Column '{col.name}' in '{table.full_name}' "
                        "has a generic name that may reduce clarity."
                    ),
                    severity="warning",
                )
            )


def lint_tables(tables: List[TableSchema]) -> LintResult:
    issues: List[LintIssue] = []
    for table in tables:
        _check_missing_primary_key(table, issues)
        _check_nullable_columns(table, issues)
        _check_generic_column_names(table, issues)
    return LintResult(issues=issues)
