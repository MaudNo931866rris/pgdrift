"""Retention policy: flag snapshots and audit records exceeding a max-age."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

_RETENTION_FILE = ".pgdrift" / Path("retention.json")


def _retention_path(base_dir: Path) -> Path:
    return base_dir / "retention.json"


@dataclass
class RetentionPolicy:
    max_snapshot_days: int = 90
    max_audit_days: int = 180


@dataclass
class RetentionViolation:
    kind: str          # "snapshot" | "audit"
    name: str          # filename or audit key
    captured_at: str
    age_days: int


@dataclass
class RetentionReport:
    policy: RetentionPolicy
    violations: List[RetentionViolation] = field(default_factory=list)

    def any_violations(self) -> bool:
        return bool(self.violations)

    def as_dict(self) -> dict:
        return {
            "policy": {
                "max_snapshot_days": self.policy.max_snapshot_days,
                "max_audit_days": self.policy.max_audit_days,
            },
            "violations": [
                {
                    "kind": v.kind,
                    "name": v.name,
                    "captured_at": v.captured_at,
                    "age_days": v.age_days,
                }
                for v in self.violations
            ],
        }


def load_retention(base_dir: Path) -> RetentionPolicy:
    path = _retention_path(base_dir)
    if not path.exists():
        return RetentionPolicy()
    data = json.loads(path.read_text())
    return RetentionPolicy(
        max_snapshot_days=data.get("max_snapshot_days", 90),
        max_audit_days=data.get("max_audit_days", 180),
    )


def save_retention(base_dir: Path, policy: RetentionPolicy) -> None:
    path = _retention_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "max_snapshot_days": policy.max_snapshot_days,
        "max_audit_days": policy.max_audit_days,
    }, indent=2))


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def evaluate_retention(
    policy: RetentionPolicy,
    snapshots: List[dict],
    audits: List[dict],
) -> RetentionReport:
    now = datetime.now(tz=timezone.utc)
    violations: List[RetentionViolation] = []

    for snap in snapshots:
        ts = _parse_ts(snap.get("captured_at", ""))
        if ts is None:
            continue
        age = (now - ts).days
        if age > policy.max_snapshot_days:
            violations.append(RetentionViolation(
                kind="snapshot",
                name=snap.get("name", "unknown"),
                captured_at=snap["captured_at"],
                age_days=age,
            ))

    for audit in audits:
        ts = _parse_ts(audit.get("captured_at", ""))
        if ts is None:
            continue
        age = (now - ts).days
        if age > policy.max_audit_days:
            violations.append(RetentionViolation(
                kind="audit",
                name=audit.get("profile", "unknown"),
                captured_at=audit["captured_at"],
                age_days=age,
            ))

    return RetentionReport(policy=policy, violations=violations)
