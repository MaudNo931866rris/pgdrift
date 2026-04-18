"""Schema maturity scoring based on drift history and lint results."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from pgdrift.lint import LintResult, has_issues, errors, warnings
from pgdrift.drift_age import DriftAgeReport
from pgdrift.summary import DriftSummary


@dataclass
class MaturityScore:
    profile: str
    score: float          # 0.0 – 100.0
    grade: str
    penalties: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "profile": self.profile,
            "score": round(self.score, 2),
            "grade": self.grade,
            "penalties": self.penalties,
        }


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def compute_maturity(
    profile: str,
    lint_result: LintResult,
    age_report: DriftAgeReport,
    summary: DriftSummary | None = None,
) -> MaturityScore:
    score = 100.0
    penalties: List[str] = []

    error_count = len(errors(lint_result))
    if error_count:
        deduction = min(40.0, error_count * 10.0)
        score -= deduction
        penalties.append(f"-{deduction:.0f} pts: {error_count} lint error(s)")

    warn_count = len(warnings(lint_result))
    if warn_count:
        deduction = min(20.0, warn_count * 5.0)
        score -= deduction
        penalties.append(f"-{deduction:.0f} pts: {warn_count} lint warning(s)")

    if age_report.entries:
        oldest = age_report.oldest
        if oldest and oldest.age_days > 30:
            deduction = min(20.0, (oldest.age_days - 30) * 0.5)
            score -= deduction
            penalties.append(f"-{deduction:.0f} pts: drift unresolved for {oldest.age_days} days")

    if summary and summary.has_destructive_changes:
        score -= 10.0
        penalties.append("-10 pts: destructive changes detected")

    score = max(0.0, score)
    return MaturityScore(profile=profile, score=score, grade=_grade(score), penalties=penalties)
