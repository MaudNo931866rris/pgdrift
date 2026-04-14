"""Unit tests for pgdrift.schedule."""

import json
import pytest
from pathlib import Path

from pgdrift import schedule as sched


@pytest.fixture
def schedule_dir(tmp_path):
    return str(tmp_path)


def test_load_returns_empty_when_no_file(schedule_dir):
    result = sched.load_schedules(schedule_dir)
    assert result == {}


def test_add_creates_schedule(schedule_dir):
    entry = sched.add_schedule("nightly", "prod", "staging", 60, directory=schedule_dir)
    assert entry["name"] == "nightly"
    assert entry["source"] == "prod"
    assert entry["target"] == "staging"
    assert entry["interval_minutes"] == 60


def test_add_persists_to_disk(schedule_dir):
    sched.add_schedule("daily", "prod", "dev", 1440, directory=schedule_dir)
    loaded = sched.load_schedules(schedule_dir)
    assert "daily" in loaded
    assert loaded["daily"]["interval_minutes"] == 1440


def test_add_overwrites_existing(schedule_dir):
    sched.add_schedule("job", "a", "b", 10, directory=schedule_dir)
    sched.add_schedule("job", "a", "b", 20, directory=schedule_dir)
    assert sched.get_schedule("job", schedule_dir)["interval_minutes"] == 20


def test_remove_existing_returns_true(schedule_dir):
    sched.add_schedule("tmp", "x", "y", 5, directory=schedule_dir)
    assert sched.remove_schedule("tmp", directory=schedule_dir) is True


def test_remove_missing_returns_false(schedule_dir):
    assert sched.remove_schedule("ghost", directory=schedule_dir) is False


def test_get_schedule_returns_none_for_missing(schedule_dir):
    assert sched.get_schedule("nope", schedule_dir) is None


def test_list_schedules_returns_all(schedule_dir):
    sched.add_schedule("a", "p", "s", 30, directory=schedule_dir)
    sched.add_schedule("b", "p", "d", 60, directory=schedule_dir)
    entries = sched.list_schedules(schedule_dir)
    names = [e["name"] for e in entries]
    assert "a" in names
    assert "b" in names


def test_schedule_file_is_valid_json(schedule_dir):
    sched.add_schedule("check", "prod", "qa", 15, directory=schedule_dir)
    path = Path(schedule_dir) / ".pgdrift_schedules.json"
    with open(path) as f:
        data = json.load(f)
    assert "check" in data
