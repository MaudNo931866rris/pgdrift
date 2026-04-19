import argparse
import pytest
from unittest.mock import patch, MagicMock
from pgdrift.commands.bloat_cmd import cmd_bloat
from pgdrift.config import Config, DatabaseProfile
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.bloat import BloatReport, BloatEntry


def _args(**kwargs):
    defaults = dict(
        config="pgdrift.yml",
        profile="dev",
        schema="public",
        max_columns=30,
        max_nullable_ratio=0.6,
        top=10,
        json=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config(profile_name="dev"):
    profile = DatabaseProfile(
        host="localhost", port=5432, user="u", password="p", dbname="db"
    )
    cfg = MagicMock(spec=Config)
    cfg.profiles = {profile_name: profile}
    return cfg


def test_missing_config_returns_1():
    with patch("pgdrift.commands.bloat_cmd.load", side_effect=FileNotFoundError):
        assert cmd_bloat(_args()) == 1


def test_unknown_profile_returns_1():
    cfg = _make_mock_config()
    with patch("pgdrift.commands.bloat_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.bloat_cmd.get_profile", return_value=None):
        assert cmd_bloat(_args(profile="missing")) == 1


def test_no_bloat_returns_0():
    cfg = _make_mock_config()
    profile = cfg.profiles["dev"]
    empty_report = BloatReport(entries=[])
    with patch("pgdrift.commands.bloat_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.bloat_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.bloat_cmd.psycopg2") as mock_pg, \
         patch("pgdrift.commands.bloat_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.bloat_cmd.compute_bloat", return_value=empty_report):
        assert cmd_bloat(_args()) == 0


def test_bloat_detected_returns_1(capsys):
    cfg = _make_mock_config()
    profile = cfg.profiles["dev"]
    entry = BloatEntry(
        table="public.fat",
        column_count=35,
        nullable_count=2,
        nullable_ratio=0.06,
        reasons=["column count 35 exceeds limit 30"],
    )
    report = BloatReport(entries=[entry])
    with patch("pgdrift.commands.bloat_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.bloat_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.bloat_cmd.psycopg2") as mock_pg, \
         patch("pgdrift.commands.bloat_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.bloat_cmd.compute_bloat", return_value=report):
        result = cmd_bloat(_args())
    assert result == 1
    out = capsys.readouterr().out
    assert "public.fat" in out
