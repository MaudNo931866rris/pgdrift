"""Tests for pgdrift.coupling."""
import json
import pytest
from unittest.mock import patch
from pgdrift.coupling import (
    CouplingPair,
    CouplingReport,
    compute_coupling,
)


def _entry(tables):
    return {"report": {"tables": [{"table": t} for t in tables]}}


def test_empty_audit_returns_empty_report():
    with patch("pgdrift.coupling.load_audit", return_value=[]):
        report = compute_coupling(".pgdrift/audit")
    assert not report.has_coupling()
    assert report.pairs == []


def test_single_snapshot_no_pairs():
    with patch("pgdrift.coupling.load_audit", return_value=[_entry(["public.users"])]):
        report = compute_coupling(".pgdrift/audit", min_co_changes=1)
    assert not report.has_coupling()


def test_detects_co_changing_pair():
    entries = [
        _entry(["public.orders", "public.items"]),
        _entry(["public.orders", "public.items"]),
    ]
    with patch("pgdrift.coupling.load_audit", return_value=entries):
        report = compute_coupling(".pgdrift/audit", min_co_changes=2)
    assert report.has_coupling()
    assert len(report.pairs) == 1
    pair = report.pairs[0]
    assert pair.table_a == "public.items"
    assert pair.table_b == "public.orders"
    assert pair.co_changes == 2


def test_coupling_ratio_calculated_correctly():
    pair = CouplingPair("a", "b", co_changes=3, total_snapshots=4)
    assert pair.coupling_ratio() == 0.75


def test_coupling_ratio_zero_when_no_snapshots():
    pair = CouplingPair("a", "b", co_changes=0, total_snapshots=0)
    assert pair.coupling_ratio() == 0.0


def test_strong_pairs_filters_by_threshold():
    pairs = [
        CouplingPair("a", "b", 4, 4),
        CouplingPair("c", "d", 1, 4),
    ]
    report = CouplingReport(pairs=pairs)
    strong = report.strong_pairs(threshold=0.5)
    assert len(strong) == 1
    assert strong[0].table_a == "a"


def test_as_dict_contains_expected_keys():
    pair = CouplingPair("x", "y", 2, 5)
    d = pair.as_dict()
    assert "table_a" in d
    assert "table_b" in d
    assert "co_changes" in d
    assert "coupling_ratio" in d


def test_min_co_changes_filters_low_pairs():
    entries = [
        _entry(["public.a", "public.b"]),
        _entry(["public.a", "public.c", "public.b"]),
        _entry(["public.a", "public.c"]),
    ]
    with patch("pgdrift.coupling.load_audit", return_value=entries):
        report = compute_coupling(".pgdrift/audit", min_co_changes=2)
    tables = {(p.table_a, p.table_b) for p in report.pairs}
    assert ("public.a", "public.b") in tables
    assert ("public.a", "public.c") in tables
