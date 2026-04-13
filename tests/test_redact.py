"""Tests for pgdrift.redact and pgdrift.commands.redact_cmd."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pgdrift import redact as redact_module
from pgdrift.commands.redact_cmd import cmd_redact_add, cmd_redact_remove, cmd_redact_list


@pytest.fixture()
def redact_dir(tmp_path: Path) -> Path:
    return tmp_path


def _args(redact_dir: Path, **kwargs) -> argparse.Namespace:
    base = {"config_dir": str(redact_dir)}
    base.update(kwargs)
    return argparse.Namespace(**base)


# --- redact module unit tests ---

def test_load_returns_empty_when_no_file(redact_dir: Path) -> None:
    rules = redact_module.load_redact_rules(redact_dir)
    assert rules == {}


def test_add_creates_rule(redact_dir: Path) -> None:
    redact_module.add_redact_rule(redact_dir, "users", "password")
    rules = redact_module.load_redact_rules(redact_dir)
    assert "password" in rules["users"]


def test_add_no_duplicates(redact_dir: Path) -> None:
    redact_module.add_redact_rule(redact_dir, "users", "token")
    redact_module.add_redact_rule(redact_dir, "users", "token")
    rules = redact_module.load_redact_rules(redact_dir)
    assert rules["users"].count("token") == 1


def test_remove_existing_returns_true(redact_dir: Path) -> None:
    redact_module.add_redact_rule(redact_dir, "accounts", "secret")
    result = redact_module.remove_redact_rule(redact_dir, "accounts", "secret")
    assert result is True
    rules = redact_module.load_redact_rules(redact_dir)
    assert "accounts" not in rules


def test_remove_missing_returns_false(redact_dir: Path) -> None:
    result = redact_module.remove_redact_rule(redact_dir, "orders", "nonexistent")
    assert result is False


def test_is_sensitive_column_detects_password() -> None:
    assert redact_module.is_sensitive_column("user_password") is True


def test_is_sensitive_column_ignores_safe_name() -> None:
    assert redact_module.is_sensitive_column("created_at") is False


def test_should_redact_via_explicit_rule(redact_dir: Path) -> None:
    redact_module.add_redact_rule(redact_dir, "payments", "card_number")
    rules = redact_module.load_redact_rules(redact_dir)
    assert redact_module.should_redact("payments", "card_number", rules) is True


def test_should_redact_via_heuristic() -> None:
    assert redact_module.should_redact("users", "api_key_value", {}) is True


# --- command tests ---

def test_cmd_add_returns_0(redact_dir: Path) -> None:
    args = _args(redact_dir, table="users", column="ssn")
    assert cmd_redact_add(args) == 0


def test_cmd_remove_existing_returns_0(redact_dir: Path) -> None:
    redact_module.add_redact_rule(redact_dir, "users", "token")
    args = _args(redact_dir, table="users", column="token")
    assert cmd_redact_remove(args) == 0


def test_cmd_remove_missing_returns_1(redact_dir: Path) -> None:
    args = _args(redact_dir, table="users", column="ghost")
    assert cmd_redact_remove(args) == 1


def test_cmd_list_returns_0(redact_dir: Path) -> None:
    args = _args(redact_dir)
    assert cmd_redact_list(args) == 0
