"""Tests for pgdrift.commands.maturity_cmd"""
import argparse
from unittest.mock import patch, MagicMock

from pgdrift.commands.maturity_cmd import cmd_maturity
from pgdrift.config import Config, DatabaseProfile
from pgdrift.maturity import MaturityScore


def _args(**kwargs):
    defaults = dict(config="pgdrift.yml", profile="prod", schema="public", json=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config(profiles=None):
    cfg = MagicMock(spec=Config)
    cfg.profiles = profiles or {"prod": DatabaseProfile(host="localhost", port=5432, dbname="db", user="u", password="p")}
    return cfg


def test_missing_config_returns_1():
    with patch("pgdrift.commands.maturity_cmd.load", side_effect=FileNotFoundError):
        assert cmd_maturity(_args()) == 1


def test_unknown_profile_returns_1():
    cfg = _make_mock_config()
    with patch("pgdrift.commands.maturity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.maturity_cmd.get_profile", return_value=None):
        assert cmd_maturity(_args(profile="ghost")) == 1


def test_maturity_returns_0(capsys):
    cfg = _make_mock_config()
    profile = cfg.profiles["prod"]
    mock_conn = MagicMock()

    with patch("pgdrift.commands.maturity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.maturity_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.maturity_cmd.psycopg2.connect", return_value=mock_conn), \
         patch("pgdrift.commands.maturity_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.maturity_cmd.lint_tables", return_value=MagicMock(issues=[])):
        rc = cmd_maturity(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "Score" in out


def test_maturity_json_output(capsys):
    import json
    cfg = _make_mock_config()
    profile = cfg.profiles["prod"]
    mock_conn = MagicMock()

    with patch("pgdrift.commands.maturity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.maturity_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.maturity_cmd.psycopg2.connect", return_value=mock_conn), \
         patch("pgdrift.commands.maturity_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.maturity_cmd.lint_tables", return_value=MagicMock(issues=[])):
        rc = cmd_maturity(_args(json=True))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "score" in data
    assert "grade" in data
