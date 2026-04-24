"""Tests for pgdrift.symmetry."""
import pytest

from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.symmetry import (
    SymmetryReport,
    as_dict,
    compute_symmetry,
    overall_score,
)


def _col(name: str, dtype: str = "text", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=dtype, is_nullable=nullable)


def _table(name: str, cols: list) -> TableSchema:
    return TableSchema(schema="public", name=name, columns=cols)


# ---------------------------------------------------------------------------
# compute_symmetry
# ---------------------------------------------------------------------------

def test_empty_schemas_return_perfect_symmetry():
    report = compute_symmetry([], [])
    assert report.table_symmetry == 1.0
    assert overall_score(report) == 1.0


def test_identical_single_table_scores_one():
    cols = [_col("id"), _col("name")]
    src = [_table("users", cols)]
    tgt = [_table("users", cols)]
    report = compute_symmetry(src, tgt)
    assert report.table_symmetry == 1.0
    assert len(report.entries) == 1
    assert report.entries[0].score == 1.0


def test_disjoint_tables_score_zero():
    src = [_table("orders", [_col("id")])]
    tgt = [_table("products", [_col("id")])]
    report = compute_symmetry(src, tgt)
    assert report.table_symmetry == 0.0
    assert report.entries == []
    assert overall_score(report) == 0.0


def test_partial_table_overlap():
    shared = _table("users", [_col("id")])
    only_src = _table("orders", [_col("id")])
    only_tgt = _table("products", [_col("id")])
    report = compute_symmetry([shared, only_src], [shared, only_tgt])
    # 1 shared out of union of 3
    assert report.table_symmetry == pytest.approx(1 / 3, rel=1e-4)


def test_partial_column_overlap():
    src = [_table("users", [_col("id"), _col("email"), _col("phone")])]
    tgt = [_table("users", [_col("id"), _col("email")])]
    report = compute_symmetry(src, tgt)
    entry = report.entries[0]
    # common=2, union=3
    assert entry.common_columns == 2
    assert entry.score == pytest.approx(2 / 3, rel=1e-4)


def test_overall_score_averages_table_and_column_symmetry():
    src = [_table("users", [_col("id"), _col("x")])]
    tgt = [_table("users", [_col("id"), _col("y")])]
    report = compute_symmetry(src, tgt)
    # table_sym=1.0, col_score=0.5 => overall=(1.0+0.5)/2=0.75
    assert overall_score(report) == pytest.approx(0.75, rel=1e-4)


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_contains_expected_keys():
    src = [_table("t", [_col("a"), _col("b")])]
    tgt = [_table("t", [_col("a"), _col("c")])]
    report = compute_symmetry(src, tgt)
    d = as_dict(report.entries[0])
    assert set(d.keys()) == {"table", "source_columns", "target_columns", "common_columns", "score"}
    assert d["table"] == "t"
