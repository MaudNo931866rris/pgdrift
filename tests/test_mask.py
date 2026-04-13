"""Tests for pgdrift.mask."""

from __future__ import annotations

import pytest

from pgdrift import mask as mask_module


@pytest.fixture()
def mask_dir(tmp_path):
    return str(tmp_path)


def test_load_returns_empty_when_no_file(mask_dir):
    result = mask_module.load_masks(mask_dir)
    assert result == {}


def test_add_creates_mask(mask_dir):
    mask_module.add_mask("ssn", "<redacted>", directory=mask_dir)
    masks = mask_module.load_masks(mask_dir)
    assert masks["ssn"] == "<redacted>"


def test_add_overwrites_existing_mask(mask_dir):
    mask_module.add_mask("email", "<email>", directory=mask_dir)
    mask_module.add_mask("email", "[email]", directory=mask_dir)
    masks = mask_module.load_masks(mask_dir)
    assert masks["email"] == "[email]"


def test_remove_existing_mask_returns_true(mask_dir):
    mask_module.add_mask("phone", "<phone>", directory=mask_dir)
    result = mask_module.remove_mask("phone", directory=mask_dir)
    assert result is True
    assert "phone" not in mask_module.load_masks(mask_dir)


def test_remove_missing_mask_returns_false(mask_dir):
    result = mask_module.remove_mask("nonexistent", directory=mask_dir)
    assert result is False


def test_list_masks_sorted(mask_dir):
    mask_module.add_mask("zzz", "z_alias", directory=mask_dir)
    mask_module.add_mask("aaa", "a_alias", directory=mask_dir)
    entries = mask_module.list_masks(mask_dir)
    assert entries[0]["column"] == "aaa"
    assert entries[1]["column"] == "zzz"


def test_apply_mask_returns_alias(mask_dir):
    masks = {"password": "<hidden>"}
    assert mask_module.apply_mask("password", masks) == "<hidden>"


def test_apply_mask_returns_original_when_no_rule():
    assert mask_module.apply_mask("created_at", {}) == "created_at"
