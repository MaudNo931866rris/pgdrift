from __future__ import annotations

import math
import pytest

from pgdrift.entropy import (
    EntropyPoint,
    EntropyReport,
    _shannon_entropy,
    _entropy_for_point,
    compute_entropy,
)
from pgdrift.trend import TrendPoint


# ---------------------------------------------------------------------------
# _shannon_entropy
# ---------------------------------------------------------------------------

def test_shannon_entropy_zero_when_no_changes():
    assert _shannon_entropy([0, 0, 0]) == 0.0


def test_shannon_entropy_zero_when_total_zero():
    assert _shannon_entropy([]) == 0.0


def test_shannon_entropy_positive_for_partial():
    result = _shannon_entropy([1, 1, 0])
    assert result > 0.0


def test_shannon_entropy_formula():
    # two equal buckets => entropy = 1.0 bit
    result = _shannon_entropy([1, 1])
    assert abs(result - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# _make_report helpers
# ---------------------------------------------------------------------------

def _make_report(added=0, removed=0, modified=0, ts="2024-01-01T00:00:00"):
    return TrendPoint(
        timestamp=ts,
        added_tables=added,
        removed_tables=removed,
        modified_tables=modified,
    )


# ---------------------------------------------------------------------------
# _entropy_for_point
# ---------------------------------------------------------------------------

def test_entropy_for_point_zero_when_no_changes():
    pt = _make_report()
    assert _entropy_for_point(pt) == 0.0


def test_entropy_for_point_positive_when_changes():
    pt = _make_report(added=1, removed=1)
    assert _entropy_for_point(pt) > 0.0


# ---------------------------------------------------------------------------
# compute_entropy
# ---------------------------------------------------------------------------

def test_compute_entropy_empty_returns_empty_report():
    report = compute_entropy([])
    assert report.points == []
    assert report.average_entropy() == 0.0
    assert report.max_entropy() == 0.0


def test_compute_entropy_single_point():
    pts = [_make_report(added=1, removed=1, modified=1)]
    report = compute_entropy(pts)
    assert len(report.points) == 1
    assert report.points[0].total_changes == 3
    assert report.points[0].entropy > 0.0


def test_compute_entropy_average_and_max():
    pts = [
        _make_report(added=2, ts="2024-01-01T00:00:00"),
        _make_report(added=1, removed=1, ts="2024-01-02T00:00:00"),
    ]
    report = compute_entropy(pts)
    assert report.max_entropy() >= report.average_entropy()


def test_as_dict_structure():
    pts = [_make_report(added=1)]
    report = compute_entropy(pts)
    d = report.as_dict()
    assert "average_entropy" in d
    assert "max_entropy" in d
    assert "points" in d
    assert d["points"][0]["total_changes"] == 1
