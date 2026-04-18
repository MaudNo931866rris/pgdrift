import json
import pytest
from pgdrift.deprecation import (
    DeprecationEntry,
    DeprecationReport,
    load_deprecations,
    save_deprecations,
    add_deprecation,
    remove_deprecation,
)


@pytest.fixture
def dep_dir(tmp_path):
    return str(tmp_path)


def _entry(schema="public", table="users", column=None, reason="old", since="2024-01-01"):
    return DeprecationEntry(schema=schema, table=table, column=column, reason=reason, since=since)


def test_load_returns_empty_when_no_file(dep_dir):
    report = load_deprecations(dep_dir)
    assert report.entries == []


def test_add_creates_entry(dep_dir):
    add_deprecation(_entry(), dep_dir)
    report = load_deprecations(dep_dir)
    assert len(report.entries) == 1
    assert report.entries[0].table == "users"


def test_add_overwrites_existing_key(dep_dir):
    add_deprecation(_entry(reason="old"), dep_dir)
    add_deprecation(_entry(reason="updated"), dep_dir)
    report = load_deprecations(dep_dir)
    assert len(report.entries) == 1
    assert report.entries[0].reason == "updated"


def test_add_column_level_deprecation(dep_dir):
    add_deprecation(_entry(column="email"), dep_dir)
    report = load_deprecations(dep_dir)
    assert report.entries[0].column == "email"
    assert report.entries[0].key() == "public.users.email"


def test_remove_existing_returns_true(dep_dir):
    add_deprecation(_entry(), dep_dir)
    result = remove_deprecation("public.users", dep_dir)
    assert result is True
    assert load_deprecations(dep_dir).entries == []


def test_remove_missing_returns_false(dep_dir):
    result = remove_deprecation("public.nonexistent", dep_dir)
    assert result is False


def test_is_deprecated_table(dep_dir):
    add_deprecation(_entry(), dep_dir)
    report = load_deprecations(dep_dir)
    assert report.is_deprecated("public", "users") is True
    assert report.is_deprecated("public", "orders") is False


def test_is_deprecated_column(dep_dir):
    add_deprecation(_entry(column="legacy_id"), dep_dir)
    report = load_deprecations(dep_dir)
    assert report.is_deprecated("public", "users", "legacy_id") is True
    assert report.is_deprecated("public", "users", "name") is False


def test_by_table_returns_matching_entries(dep_dir):
    add_deprecation(_entry(column="col1"), dep_dir)
    add_deprecation(_entry(column="col2"), dep_dir)
    add_deprecation(_entry(table="orders", column="total"), dep_dir)
    report = load_deprecations(dep_dir)
    result = report.by_table("public", "users")
    assert len(result) == 2
