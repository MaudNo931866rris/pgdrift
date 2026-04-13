"""Unit tests for pgdrift.tags."""

import json
import pytest
from pathlib import Path

from pgdrift import tags as tag_store


@pytest.fixture
def tag_dir(tmp_path):
    return str(tmp_path)


def test_load_returns_empty_when_no_file(tag_dir):
    result = tag_store.load_tags(tag_dir)
    assert result == {}


def test_add_creates_tag(tag_dir):
    tag_store.add_tag("v1", "snapshot_prod_20240101.json", directory=tag_dir)
    tags = tag_store.load_tags(tag_dir)
    assert tags["v1"] == "snapshot_prod_20240101.json"


def test_add_overwrites_existing_tag(tag_dir):
    tag_store.add_tag("stable", "old.json", directory=tag_dir)
    tag_store.add_tag("stable", "new.json", directory=tag_dir)
    assert tag_store.load_tags(tag_dir)["stable"] == "new.json"


def test_remove_existing_tag_returns_true(tag_dir):
    tag_store.add_tag("v2", "snap.json", directory=tag_dir)
    result = tag_store.remove_tag("v2", directory=tag_dir)
    assert result is True
    assert "v2" not in tag_store.load_tags(tag_dir)


def test_remove_missing_tag_returns_false(tag_dir):
    result = tag_store.remove_tag("ghost", directory=tag_dir)
    assert result is False


def test_resolve_returns_filename(tag_dir):
    tag_store.add_tag("prod-baseline", "baseline_prod.json", directory=tag_dir)
    assert tag_store.resolve_tag("prod-baseline", directory=tag_dir) == "baseline_prod.json"


def test_resolve_returns_none_for_missing(tag_dir):
    assert tag_store.resolve_tag("nope", directory=tag_dir) is None


def test_list_tags_sorted(tag_dir):
    tag_store.add_tag("z-tag", "z.json", directory=tag_dir)
    tag_store.add_tag("a-tag", "a.json", directory=tag_dir)
    entries = tag_store.list_tags(tag_dir)
    assert entries[0]["tag"] == "a-tag"
    assert entries[1]["tag"] == "z-tag"


def test_save_creates_valid_json(tag_dir):
    tag_store.add_tag("check", "file.json", directory=tag_dir)
    tags_file = Path(tag_dir) / ".pgdrift_tags.json"
    assert tags_file.exists()
    data = json.loads(tags_file.read_text())
    assert data["check"] == "file.json"
