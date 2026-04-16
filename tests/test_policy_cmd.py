"""Tests for pgdrift.commands.policy_cmd."""
import types
import pytest
from pathlib import Path
from pgdrift.commands.policy_cmd import cmd_policy_save, cmd_policy_list, cmd_policy_delete
from pgdrift.policy import load_policy


@pytest.fixture()
def policy_dir(tmp_path):
    return tmp_path / "policies"


def _args(policy_dir, **kwargs):
    ns = types.SimpleNamespace(
        policy_dir=str(policy_dir),
        name="default",
        max_added=None,
        max_removed=None,
        max_modified=None,
        no_destructive=False,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_save_returns_0(policy_dir):
    assert cmd_policy_save(_args(policy_dir)) == 0


def test_save_persists_policy(policy_dir):
    cmd_policy_save(_args(policy_dir, name="mypolicy", max_added=3))
    rule = load_policy("mypolicy", policy_dir)
    assert rule is not None
    assert rule.max_added_tables == 3


def test_save_no_destructive(policy_dir):
    cmd_policy_save(_args(policy_dir, name="strict", no_destructive=True))
    rule = load_policy("strict", policy_dir)
    assert rule.allow_destructive is False


def test_list_no_policies(policy_dir, capsys):
    rc = cmd_policy_list(_args(policy_dir))
    assert rc == 0
    assert "No policies" in capsys.readouterr().out


def test_list_shows_saved(policy_dir, capsys):
    cmd_policy_save(_args(policy_dir, name="pol1"))
    cmd_policy_list(_args(policy_dir))
    assert "pol1" in capsys.readouterr().out


def test_delete_existing_returns_0(policy_dir):
    cmd_policy_save(_args(policy_dir, name="del_me"))
    rc = cmd_policy_delete(_args(policy_dir, name="del_me"))
    assert rc == 0


def test_delete_missing_returns_1(policy_dir):
    rc = cmd_policy_delete(_args(policy_dir, name="ghost"))
    assert rc == 1
