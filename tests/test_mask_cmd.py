"""Tests for pgdrift.commands.mask_cmd."""

from __future__ import annotations

import argparse

import pytest

from pgdrift import mask as mask_module
from pgdrift.commands import mask_cmd


@pytest.fixture()
def mask_dir(tmp_path):
    return str(tmp_path)


def _args(**kwargs):
    defaults = {"dir": "."}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_returns_0(mask_dir, capsys):
    args = _args(column="ssn", alias="<redacted>", dir=mask_dir)
    rc = mask_cmd.cmd_mask_add(args)
    assert rc == 0


def test_add_persists_mask(mask_dir):
    args = _args(column="email", alias="<email>", dir=mask_dir)
    mask_cmd.cmd_mask_add(args)
    masks = mask_module.load_masks(mask_dir)
    assert masks["email"] == "<email>"


def test_remove_existing_returns_0(mask_dir):
    mask_module.add_mask("phone", "<phone>", directory=mask_dir)
    args = _args(column="phone", dir=mask_dir)
    rc = mask_cmd.cmd_mask_remove(args)
    assert rc == 0


def test_remove_missing_returns_1(mask_dir):
    args = _args(column="nonexistent", dir=mask_dir)
    rc = mask_cmd.cmd_mask_remove(args)
    assert rc == 1


def test_list_empty_returns_0(mask_dir, capsys):
    args = _args(dir=mask_dir)
    rc = mask_cmd.cmd_mask_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No masks" in out


def test_list_shows_entries(mask_dir, capsys):
    mask_module.add_mask("ssn", "<ssn>", directory=mask_dir)
    args = _args(dir=mask_dir)
    mask_cmd.cmd_mask_list(args)
    out = capsys.readouterr().out
    assert "ssn" in out
    assert "<ssn>" in out
