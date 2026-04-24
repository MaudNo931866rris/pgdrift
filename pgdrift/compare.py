"""Compare a live schema against a saved baseline or snapshot."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from pgdrift.diff import DriftReport, diff_schemas
from pgdrift.inspector import TableSchema
from pgdrift.baseline import load_baseline
from pgdrift.snapshot import load_snapshot


@dataclass
class CompareResult:
    source: str
    reference: str
    reference_type: str  # 'baseline' | 'snapshot'
    report: DriftReport

    @property
    def has_drift(self) -> bool:
        """Return True if the report contains any drift."""
        return bool(
            self.report.added_tables
            or self.report.removed_tables
            or self.report.modified_tables
        )


def compare_against_baseline(
    live_tables: Dict[str, TableSchema],
    profile: str,
    label: str,
    baselines_dir: Optional[str] = None,
) -> Optional[CompareResult]:
    """Diff live tables against a saved baseline.

    Returns None if no baseline exists for the given profile and label.
    """
    saved = load_baseline(profile, label, baselines_dir=baselines_dir)
    if saved is None:
        return None
    report = diff_schemas(saved, live_tables, source=label, target=profile)
    return CompareResult(
        source=profile,
        reference=label,
        reference_type="baseline",
        report=report,
    )


def compare_against_snapshot(
    live_tables: Dict[str, TableSchema],
    profile: str,
    snapshot_path: str,
) -> Optional[CompareResult]:
    """Diff live tables against a saved snapshot file.

    Returns None if the snapshot file cannot be loaded.
    """
    saved = load_snapshot(snapshot_path)
    if saved is None:
        return None
    report = diff_schemas(saved, live_tables, source=snapshot_path, target=profile)
    return CompareResult(
        source=profile,
        reference=snapshot_path,
        reference_type="snapshot",
        report=report,
    )
