"""Tests for pgdrift.annotate."""

import pytest

from pgdrift import annotate


@pytest.fixture(autouse=True)
def annotate_dir(tmp_path, monkeypatch):
    """Redirect annotation storage to a temp directory."""
    monkeypatch.setattr(annotate, "_ANNOTATIONS_DIR", tmp_path / "annotations")
    return tmp_path / "annotations"


def test_load_returns_empty_when_no_file():
    result = annotate.load_annotations("prod")
    assert result == {}


def test_add_creates_annotation():
    annotate.add_annotation("prod", "users", "Core user table")
    result = annotate.load_annotations("prod")
    assert result["users"] == "Core user table"


def test_add_overwrites_existing_annotation():
    annotate.add_annotation("prod", "users", "old note")
    annotate.add_annotation("prod", "users", "new note")
    assert annotate.get_annotation("prod", "users") == "new note"


def test_add_column_annotation():
    annotate.add_annotation("prod", "users.email", "PII — handle with care")
    assert annotate.get_annotation("prod", "users.email") == "PII — handle with care"


def test_remove_existing_annotation_returns_true():
    annotate.add_annotation("prod", "orders", "Order table")
    result = annotate.remove_annotation("prod", "orders")
    assert result is True
    assert annotate.get_annotation("prod", "orders") is None


def test_remove_missing_annotation_returns_false():
    result = annotate.remove_annotation("prod", "nonexistent")
    assert result is False


def test_list_annotations_returns_all():
    annotate.add_annotation("staging", "users", "note a")
    annotate.add_annotation("staging", "orders", "note b")
    result = annotate.list_annotations("staging")
    assert len(result) == 2
    assert result["users"] == "note a"
    assert result["orders"] == "note b"


def test_profiles_are_isolated():
    annotate.add_annotation("prod", "users", "prod note")
    annotate.add_annotation("staging", "users", "staging note")
    assert annotate.get_annotation("prod", "users") == "prod note"
    assert annotate.get_annotation("staging", "users") == "staging note"


def test_roundtrip_preserves_all_entries():
    data = {"users": "note1", "orders.total": "note2", "products": "note3"}
    for key, note in data.items():
        annotate.add_annotation("prod", key, note)
    loaded = annotate.load_annotations("prod")
    assert loaded == data
