"""Unit tests for pgdrift.commands.schedule_cmd."""

import argparse
import pytest

from pgdrift.commands.schedule_cmd import (
    cmd_schedule_add,
    cmd_schedule_remove,
    cmd_schedule_list,
    cmd_schedule_show,
)
from pgdrift import schedule as sched


@pytest.fixture
def sched_dir(tmp_path):
    return str(tmp_path)


def _args(**kwargs):
    defaults = {"dir": "."}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_returns_0(sched_dir):
    args = _args(name="nightly", source="prod", target="staging", interval=60, dir=sched_dir)
    assert cmd_schedule_add(args) == 0


def test_add_invalid_interval_returns_1(sched_dir, capsys):
    args = _args(name="bad", source="a", target="b", interval=0, dir=sched_dir)
    assert cmd_schedule_add(args) == 1
    captured = capsys.readouterr()
    assert "interval" in captured.err


def test_add_persists_schedule(sched_dir):
    args = _args(name="daily", source="prod", target="dev", interval=1440, dir=sched_dir)
    cmd_schedule_add(args)
    entry = sched.get_schedule("daily", sched_dir)
    assert entry is not None
    assert entry["interval_minutes"] == 1440


def test_remove_existing_returns_0(sched_dir):
    sched.add_schedule("tmp", "a", "b", 5, directory=sched_dir)
    args = _args(name="tmp", dir=sched_dir)
    assert cmd_schedule_remove(args) == 0


def test_remove_missing_returns_1(sched_dir, capsys):
    args = _args(name="ghost", dir=sched_dir)
    assert cmd_schedule_remove(args) == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_list_empty_returns_0(sched_dir, capsys):
    args = _args(dir=sched_dir)
    assert cmd_schedule_list(args) == 0
    captured = capsys.readouterr()
    assert "No schedules" in captured.out


def test_list_shows_entries(sched_dir, capsys):
    sched.add_schedule("weekly", "prod", "qa", 10080, directory=sched_dir)
    args = _args(dir=sched_dir)
    cmd_schedule_list(args)
    captured = capsys.readouterr()
    assert "weekly" in captured.out


def test_show_existing_prints_json(sched_dir, capsys):
    sched.add_schedule("show_me", "x", "y", 30, directory=sched_dir)
    args = _args(name="show_me", dir=sched_dir)
    assert cmd_schedule_show(args) == 0
    captured = capsys.readouterr()
    assert "show_me" in captured.out


def test_show_missing_returns_1(sched_dir, capsys):
    args = _args(name="nope", dir=sched_dir)
    assert cmd_schedule_show(args) == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err
