"""Tests for pgdrift.commands.scorecard_cmd."""
import argparse
import json
from unittest.mock import MagicMock, patch

from pgdrift.commands.scorecard_cmd import cmd_scorecard
from pgdrift.diff import DriftReport
from pgdrift.scorecard import ScorecardResult


def _args(**kwargs):
    defaults = dict(
        config="pgdrift.yml",
        source="prod",
        target="staging",
        schemas=None,
        json=False,
        min_score=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config():
    profile = MagicMock()
    profile.dsn = "postgresql://localhost/test"
    cfg = MagicMock()
    cfg.get_profile.return_value = profile
    return cfg


def _empty_report():
    return DriftReport(
        source="prod", target="staging",
        added_tables=[], removed_tables=[], modified_tables=[]
    )


def test_missing_config_returns_1():
    with patch("pgdrift.commands.scorecard_cmd.load", side_effect=FileNotFoundError):
        assert cmd_scorecard(_args()) == 1


def test_unknown_source_profile_returns_1():
    cfg = MagicMock()
    cfg.get_profile.side_effect = KeyError("prod")
    with patch("pgdrift.commands.scorecard_cmd.load", return_value=cfg):
        assert cmd_scorecard(_args()) == 1


def test_unknown_target_profile_returns_1():
    profile = MagicMock(dsn="postgresql://localhost/test")
    cfg = MagicMock()
    cfg.get_profile.side_effect = [profile, KeyError("staging")]
    with patch("pgdrift.commands.scorecard_cmd.load", return_value=cfg):
        assert cmd_scorecard(_args()) == 1


def test_no_drift_returns_0(capsys):
    cfg = _make_mock_config()
    report = _empty_report()
    card = ScorecardResult(
        source="prod", target="staging",
        total_tables=3, added_tables=0, removed_tables=0,
        modified_tables=0, total_column_changes=0,
        score=100.0, grade="A"
    )
    with patch("pgdrift.commands.scorecard_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.scorecard_cmd.psycopg2"), \
         patch("pgdrift.commands.scorecard_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.scorecard_cmd.compute_drift", return_value=report), \
         patch("pgdrift.commands.scorecard_cmd.compute_scorecard", return_value=card):
        result = cmd_scorecard(_args())
    assert result == 0


def test_json_output_is_valid_json(capsys):
    cfg = _make_mock_config()
    report = _empty_report()
    card = ScorecardResult(
        source="prod", target="staging",
        total_tables=2, added_tables=0, removed_tables=0,
        modified_tables=0, total_column_changes=0,
        score=100.0, grade="A"
    )
    with patch("pgdrift.commands.scorecard_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.scorecard_cmd.psycopg2"), \
         patch("pgdrift.commands.scorecard_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.scorecard_cmd.compute_drift", return_value=report), \
         patch("pgdrift.commands.scorecard_cmd.compute_scorecard", return_value=card):
        cmd_scorecard(_args(json=True))
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["grade"] == "A"
    assert parsed["score"] == 100.0
