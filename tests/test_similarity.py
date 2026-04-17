"""Tests for pgdrift.similarity."""
import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.similarity import compute_similarity, _table_similarity, SimilarityResult


def _col(name: str) -> ColumnInfo:
    return ColumnInfo(name=name, data_type="text", is_nullable=True)


def _table(schema: str, name: str, cols: list[str]) -> TableSchema:
    return TableSchema(schema=schema, name=name, columns=[_col(c) for c in cols])


def test_identical_tables_score_one():
    a = _table("public", "users", ["id", "email"])
    result = compute_similarity([a], [a])
    assert result.score == pytest.approx(1.0)
    assert result.matched == 1


def test_completely_different_columns_score_zero():
    a = _table("public", "users", ["id", "email"])
    b = _table("public", "users", ["foo", "bar"])
    s = _table_similarity(a, b)
    assert s == pytest.approx(0.0)


def test_partial_overlap():
    a = _table("public", "t", ["id", "name", "email"])
    b = _table("public", "t", ["id", "name", "phone"])
    s = _table_similarity(a, b)
    # intersection=2, union=4
    assert s == pytest.approx(0.5)


def test_missing_table_scores_zero():
    a = _table("public", "orders", ["id"])
    b = _table("public", "users", ["id"])
    result = compute_similarity([a], [b])
    assert result.per_table["public.orders"] == pytest.approx(0.0)
    assert result.per_table["public.users"] == pytest.approx(0.0)
    assert result.matched == 0


def test_empty_inputs_return_perfect_score():
    result = compute_similarity([], [])
    assert result.score == pytest.approx(1.0)
    assert result.total == 0


def test_as_dict_contains_expected_keys():
    a = _table("public", "t", ["id"])
    result = compute_similarity([a], [a])
    d = result.as_dict()
    assert "score" in d
    assert "matched" in d
    assert "total" in d
    assert "per_table" in d


def test_score_between_zero_and_one():
    a = _table("public", "a", ["x", "y"])
    b = _table("public", "a", ["y", "z"])
    c = _table("public", "b", ["id"])
    result = compute_similarity([a, c], [b])
    assert 0.0 <= result.score <= 1.0
