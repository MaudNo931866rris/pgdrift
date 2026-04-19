"""Tests for pgdrift.entropy."""
import json
import math
import os
import pytest

from pgdrift.entropy import (
    EntropyPoint,
    EntropyReport,
    _shannon_entropy,
    compute_entropy,
)


# ---------------------------------------------------------------------------
# unit helpers
# ---------------------------------------------------------------------------

def test_shannon_entropy_zero_when_no_changes():
    assert _shannon_entropy(0, 10) == 0.0


def test_shannon_entropy_zero_when_total_zero():
    assert _shannon_entropy(5, 0) == 0.0


def test_shannon_entropy_positive_for_partial():
    val = _shannon_entropy(3, 10)
    assert val > 0.0


def test_shannon_entropy_formula():
    p = 4 / 10
    expected = -p * math.log2(p)
    assert abs(_shannon_entropy(4, 10) - expected) < 1e-9


# ---------------------------------------------------------------------------
# EntropyReport helpers
# ---------------------------------------------------------------------------

def _make_report(*changes):
    points = [
        EntropyPoint(snapshot_id=f"s{i}", captured_at="2024-01-01T00:00:00",
                     changes=c, entropy=float(c))
        for i, c in enumerate(changes)
    ]
    return EntropyReport(points=points)


def test_average_entropy_empty():
    assert EntropyReport().average_entropy() == 0.0


def test_average_entropy_calculated():
    r = _make_report(2.0, 4.0)
    assert r.average_entropy() == pytest.approx(3.0)


def test_max_entropy_none_when_empty():
    assert EntropyReport().max_entropy() is None


def test_max_entropy_returns_highest():
    r = _make_report(1.0, 5.0, 3.0)
    assert r.max_entropy().entropy == 5.0


def test_as_dict_structure():
    r = _make_report(2.0)
    d = r.as_dict()
    assert "average_entropy" in d
    assert "max_entropy" in d
    assert "points" in d
    assert len(d["points"]) == 1


# ---------------------------------------------------------------------------
# compute_entropy integration
# ---------------------------------------------------------------------------

def test_empty_audit_returns_empty_report(tmp_path):
    report = compute_entropy(str(tmp_path))
    assert report.points == []


def test_compute_entropy_creates_points(tmp_path):
    records = [
        {"snapshot_id": "a", "captured_at": "2024-01-01T00:00:00", "total_changes": 3},
        {"snapshot_id": "b", "captured_at": "2024-01-02T00:00:00", "total_changes": 7},
    ]
    audit_file = tmp_path / "audit.json"
    audit_file.write_text(json.dumps(records))
    report = compute_entropy(str(tmp_path))
    assert len(report.points) == 2
    assert all(p.entropy >= 0 for p in report.points)
