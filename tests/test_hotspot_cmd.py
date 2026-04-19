"""Tests for pgdrift.commands.hotspot_cmd."""
import argparse
import pytest
from unittest.mock import patch, MagicMock
from pgdrift.commands.hotspot_cmd import cmd_hotspot
from pgdrift.hotspot import HotspotReport, HotspotEntry


def _args(**kwargs):
    defaults = {
        "config": "pgdrift.yml",
        "profile": None,
        "top": 5,
        "json": False,
        "snapshots_dir": ".",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config(profiles=("prod",)):
    cfg = MagicMock()
    cfg.profiles = [MagicMock(name=p) for p in profiles]
    for p, name in zip(cfg.profiles, profiles):
        p.name = name
    return cfg


def test_missing_config_returns_1():
    with patch("pgdrift.commands.hotspot_cmd.load", side_effect=FileNotFoundError):
        assert cmd_hotspot(_args()) == 1


def test_unknown_profile_returns_1():
    with patch("pgdrift.commands.hotspot_cmd.load", return_value=_make_mock_config(["prod"])):
        assert cmd_hotspot(_args(profile="staging")) == 1


def test_no_hotspot_data_returns_0(capsys):
    with patch("pgdrift.commands.hotspot_cmd.load", return_value=_make_mock_config(["prod"])):
        with patch("pgdrift.commands.hotspot_cmd.compute_hotspots", return_value=HotspotReport()):
            result = cmd_hotspot(_args(profile="prod"))
    assert result == 0
    assert "No hotspot" in capsys.readouterr().out


def test_hotspot_prints_table(capsys):
    report = HotspotReport(entries=[HotspotEntry("orders", 3, {"status": 2})])
    with patch("pgdrift.commands.hotspot_cmd.load", return_value=_make_mock_config(["prod"])):
        with patch("pgdrift.commands.hotspot_cmd.compute_hotspots", return_value=report):
            result = cmd_hotspot(_args(profile="prod"))
    out = capsys.readouterr().out
    assert result == 0
    assert "orders" in out
    assert "status" in out


def test_hotspot_json_flag(capsys):
    report = HotspotReport(entries=[HotspotEntry("users", 1, {})])
    with patch("pgdrift.commands.hotspot_cmd.load", return_value=_make_mock_config(["prod"])):
        with patch("pgdrift.commands.hotspot_cmd.compute_hotspots", return_value=report):
            result = cmd_hotspot(_args(profile="prod", json=True))
    out = capsys.readouterr().out
    assert result == 0
    assert "entries" in out
