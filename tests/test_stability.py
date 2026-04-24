"""Tests for pgdrift.stability."""
from __future__ import annotations

from unittest.mock import patch

from pgdrift.stability import (
    StabilityEntry,
    StabilityReport,
    _score,
    compute_stability,
)


# ---------------------------------------------------------------------------
# _score helper
# ---------------------------------------------------------------------------

def test_score_zero_snapshots_returns_one():
    assert _score(0, 0) == 1.0


def test_score_no_changes_returns_one():
    assert _score(0, 10) == 1.0


def test_score_all_changed_returns_zero():
    assert _score(10, 10) == 0.0


def test_score_half_changed():
    assert _score(5, 10) == 0.5


# ---------------------------------------------------------------------------
# StabilityReport helpers
# ---------------------------------------------------------------------------

def _entry(table: str, changes: int, snapshots: int) -> StabilityEntry:
    return StabilityEntry(
        table=table,
        change_count=changes,
        snapshot_count=snapshots,
        stability_score=_score(changes, snapshots),
    )


def test_most_stable_returns_highest_scores():
    report = StabilityReport(entries=[
        _entry("a", 1, 10),
        _entry("b", 9, 10),
        _entry("c", 5, 10),
    ])
    top = report.most_stable(2)
    assert top[0].table == "a"
    assert top[1].table == "c"


def test_least_stable_returns_lowest_scores():
    report = StabilityReport(entries=[
        _entry("a", 1, 10),
        _entry("b", 9, 10),
    ])
    bottom = report.least_stable(1)
    assert bottom[0].table == "b"


def test_average_score_empty_returns_one():
    assert StabilityReport().average_score() == 1.0


def test_average_score_calculated():
    report = StabilityReport(entries=[
        _entry("a", 0, 10),
        _entry("b", 10, 10),
    ])
    assert report.average_score() == 0.5


# ---------------------------------------------------------------------------
# compute_stability
# ---------------------------------------------------------------------------

_AUDIT_RECORDS = [
    {"tables": [{"table": "public.users"}, {"table": "public.orders"}]},
    {"tables": [{"table": "public.users"}]},
    {"tables": []},
]


def test_empty_audit_returns_empty_report():
    with patch("pgdrift.stability.load_audit", return_value=[]):
        report = compute_stability()
    assert report.entries == []


def test_compute_stability_counts_changes():
    with patch("pgdrift.stability.load_audit", return_value=_AUDIT_RECORDS):
        report = compute_stability()

    tables = {e.table: e for e in report.entries}
    assert tables["public.users"].change_count == 2
    assert tables["public.orders"].change_count == 1


def test_compute_stability_snapshot_count():
    with patch("pgdrift.stability.load_audit", return_value=_AUDIT_RECORDS):
        report = compute_stability()
    for entry in report.entries:
        assert entry.snapshot_count == 3


def test_as_dict_structure():
    with patch("pgdrift.stability.load_audit", return_value=_AUDIT_RECORDS):
        report = compute_stability()
    d = report.as_dict()
    assert "average_score" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)
