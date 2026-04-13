"""Tests for pgdrift.ignore module."""

from __future__ import annotations

import json
import pytest

from pgdrift import ignore as ig


@pytest.fixture()
def ignore_dir(tmp_path):
    return str(tmp_path)


def test_load_returns_empty_when_no_file(ignore_dir):
    rules = ig.load_ignore(ignore_dir)
    assert rules == {"tables": [], "columns": []}


def test_add_table_rule_persists(ignore_dir):
    ig.add_table_rule("public.audit_*", ignore_dir)
    rules = ig.load_ignore(ignore_dir)
    assert "public.audit_*" in rules["tables"]


def test_add_column_rule_persists(ignore_dir):
    ig.add_column_rule("public.users.created_at", ignore_dir)
    rules = ig.load_ignore(ignore_dir)
    assert "public.users.created_at" in rules["columns"]


def test_add_table_rule_no_duplicates(ignore_dir):
    ig.add_table_rule("public.logs", ignore_dir)
    ig.add_table_rule("public.logs", ignore_dir)
    rules = ig.load_ignore(ignore_dir)
    assert rules["tables"].count("public.logs") == 1


def test_remove_existing_rule_returns_true(ignore_dir):
    ig.add_table_rule("public.tmp_*", ignore_dir)
    result = ig.remove_rule("public.tmp_*", ignore_dir)
    assert result is True
    rules = ig.load_ignore(ignore_dir)
    assert "public.tmp_*" not in rules["tables"]


def test_remove_missing_rule_returns_false(ignore_dir):
    result = ig.remove_rule("nonexistent", ignore_dir)
    assert result is False


def test_is_table_ignored_matches_glob():
    rules = {"tables": ["public.audit_*"], "columns": []}
    assert ig.is_table_ignored("public.audit_log", rules) is True
    assert ig.is_table_ignored("public.users", rules) is False


def test_is_column_ignored_matches_qualified_glob():
    rules = {"tables": [], "columns": ["public.users.*"]}
    assert ig.is_column_ignored("public.users", "email", rules) is True
    assert ig.is_column_ignored("public.orders", "email", rules) is False


def test_is_table_ignored_exact_match():
    rules = {"tables": ["public.sessions"], "columns": []}
    assert ig.is_table_ignored("public.sessions", rules) is True


def test_save_and_reload_roundtrip(ignore_dir):
    ig.add_table_rule("public.t1", ignore_dir)
    ig.add_column_rule("public.t1.col", ignore_dir)
    rules = ig.load_ignore(ignore_dir)
    assert "public.t1" in rules["tables"]
    assert "public.t1.col" in rules["columns"]
