"""Health check module: summarises overall schema health across profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pgdrift.lint import LintResult, has_issues, errors, warnings
from pgdrift.scorecard import ScorecardResult, compute_scorecard
from pgdrift.summary import DriftSummary, build_summary
from pgdrift.diff import DriftReport
from pgdrift.inspector import TableSchema


@dataclass
class HealthReport:
    profile: str
    scorecard: ScorecardResult
    summary: Optional[DriftSummary]
    lint: LintResult
    grade: str = field(init=False)

    def __post_init__(self) -> None:
        self.grade = _overall_grade(self.scorecard.score, self.lint)

    def as_dict(self) -> dict:
        return {
            "profile": self.profile,
            "grade": self.grade,
            "score": self.scorecard.score,
            "scorecard_grade": self.scorecard.grade,
            "lint_errors": len(errors(self.lint)),
            "lint_warnings": len(warnings(self.lint)),
            "total_changes": self.summary.total_changes if self.summary else 0,
            "has_destructive": self.summary.has_destructive_changes if self.summary else False,
        }


def _overall_grade(score: float, lint: LintResult) -> str:
    error_count = len(errors(lint))
    if error_count > 0:
        score = max(0.0, score - error_count * 5)
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def compute_health(
    profile: str,
    report: DriftReport,
    tables: List[TableSchema],
) -> HealthReport:
    scorecard = compute_scorecard(report)
    summary = build_summary(report)
    from pgdrift.lint import run_lint
    lint = run_lint(tables)
    return HealthReport(profile=profile, scorecard=scorecard, summary=summary, lint=lint)
