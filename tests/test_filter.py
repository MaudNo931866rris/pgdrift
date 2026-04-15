"""Tests for pgdrift.filter module."""

import pytest

from pgdrift import filter as fil


@pytest.fixture()
def filter_dir(tmp_path):
    return str(tmp_path)


def test_load_returns_empty_when_no_file(filter_dir):
    result = fil.load_filters(filter_dir)
    assert result == {"schemas": [], "tables": []}


def test_add_schema_filter_persists(filter_dir):
    fil.add_schema_filter("public", filter_dir)
    result = fil.load_filters(filter_dir)
    assert "public" in result["schemas"]


def test_add_table_filter_persists(filter_dir):
    fil.add_table_filter("public.orders_*", filter_dir)
    result = fil.load_filters(filter_dir)
    assert "public.orders_*" in result["tables"]


def test_add_schema_filter_no_duplicates(filter_dir):
    fil.add_schema_filter("public", filter_dir)
    fil.add_schema_filter("public", filter_dir)
    result = fil.load_filters(filter_dir)
    assert result["schemas"].count("public") == 1


def test_remove_existing_schema_returns_true(filter_dir):
    fil.add_schema_filter("audit", filter_dir)
    removed = fil.remove_filter("audit", "schema", filter_dir)
    assert removed is True
    result = fil.load_filters(filter_dir)
    assert "audit" not in result["schemas"]


def test_remove_missing_returns_false(filter_dir):
    removed = fil.remove_filter("nonexistent", "schema", filter_dir)
    assert removed is False


def test_is_table_included_no_filters(filter_dir):
    assert fil.is_table_included("public", "users", filter_dir) is True


def test_is_table_excluded_by_schema(filter_dir):
    fil.add_schema_filter("public", filter_dir)
    assert fil.is_table_included("audit", "logs", filter_dir) is False
    assert fil.is_table_included("public", "users", filter_dir) is True


def test_is_table_excluded_by_pattern(filter_dir):
    fil.add_table_filter("public.orders_*", filter_dir)
    assert fil.is_table_included("public", "orders_2024", filter_dir) is True
    assert fil.is_table_included("public", "users", filter_dir) is False
