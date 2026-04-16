"""Policy enforcement: define rules that must pass on a DriftReport."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pgdrift.diff import DriftReport


@dataclass
class PolicyRule:
    name: str
    max_added_tables: Optional[int] = None
    max_removed_tables: Optional[int] = None
    max_modified_tables: Optional[int] = None
    allow_destructive: bool = True


@dataclass
class PolicyViolation:
    rule: str
    message: str


@dataclass
class PolicyResult:
    passed: bool
    violations: List[PolicyViolation] = field(default_factory=list)


def _policy_path(name: str, base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{name}.json"


def save_policy(rule: PolicyRule, base: Path) -> None:
    path = _policy_path(rule.name, base)
    path.write_text(json.dumps({
        "name": rule.name,
        "max_added_tables": rule.max_added_tables,
        "max_removed_tables": rule.max_removed_tables,
        "max_modified_tables": rule.max_modified_tables,
        "allow_destructive": rule.allow_destructive,
    }, indent=2))


def load_policy(name: str, base: Path) -> Optional[PolicyRule]:
    path = _policy_path(name, base)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return PolicyRule(**data)


def list_policies(base: Path) -> List[str]:
    if not base.exists():
        return []
    return [p.stem for p in sorted(base.glob("*.json"))]


def delete_policy(name: str, base: Path) -> bool:
    path = _policy_path(name, base)
    if not path.exists():
        return False
    path.unlink()
    return True


def evaluate_policy(rule: PolicyRule, report: DriftReport) -> PolicyResult:
    violations: List[PolicyViolation] = []
    added = len(report.added_tables)
    removed = len(report.removed_tables)
    modified = len(report.modified_tables)

    if rule.max_added_tables is not None and added > rule.max_added_tables:
        violations.append(PolicyViolation(rule.name, f"Added tables {added} exceeds limit {rule.max_added_tables}"))
    if rule.max_removed_tables is not None and removed > rule.max_removed_tables:
        violations.append(PolicyViolation(rule.name, f"Removed tables {removed} exceeds limit {rule.max_removed_tables}"))
    if rule.max_modified_tables is not None and modified > rule.max_modified_tables:
        violations.append(PolicyViolation(rule.name, f"Modified tables {modified} exceeds limit {rule.max_modified_tables}"))
    if not rule.allow_destructive and removed > 0:
        violations.append(PolicyViolation(rule.name, "Destructive changes (removed tables) are not allowed"))

    return PolicyResult(passed=len(violations) == 0, violations=violations)
