"""Tests for pgdrift.commands.shadow_cmd."""
import argparse
from unittest.mock import patch, MagicMock
from pgdrift.commands.shadow_cmd import cmd_shadow
from pgdrift.shadow import ShadowReport


def _args(**kwargs):
    defaults = dict(config="pgdrift.yml", profile="prod", pin="v1", json=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config(profile_name="prod"):
    profile = MagicMock()
    profile.dsn = "postgresql://localhost/test"
    cfg = MagicMock()
    with patch("pgdrift.commands.shadow_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.shadow_cmd.get_profile", return_value=profile):
        yield cfg, profile


def test_missing_config_returns_1():
    with patch("pgdrift.commands.shadow_cmd.load", return_value=None):
        assert cmd_shadow(_args()) == 1


def test_unknown_profile_returns_1():
    cfg = MagicMock()
    with patch("pgdrift.commands.shadow_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.shadow_cmd.get_profile", return_value=None):
        assert cmd_shadow(_args()) == 1


def test_no_shadow_returns_0(capsys):
    profile = MagicMock(dsn="postgresql://localhost/test")
    cfg = MagicMock()
    conn = MagicMock()
    with patch("pgdrift.commands.shadow_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.shadow_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.shadow_cmd.psycopg2.connect", return_value=conn), \
         patch("pgdrift.commands.shadow_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.shadow_cmd.compute_shadow", return_value=ShadowReport()):
        result = cmd_shadow(_args())
    assert result == 0
    out = capsys.readouterr().out
    assert "No shadow drift" in out


def test_shadow_detected_returns_1(capsys):
    from pgdrift.shadow import ShadowEntry
    from pgdrift.diff import TableDiff, ColumnInfo
    col = ColumnInfo(name="email", data_type="text", is_nullable=False)
    td = TableDiff(name="public.users", added_columns=[col], removed_columns=[], modified_columns=[])
    entry = ShadowEntry(table="public.users", pin_label="v1", drift=td)
    report = ShadowReport(entries=[entry])
    profile = MagicMock(dsn="postgresql://localhost/test")
    cfg = MagicMock()
    conn = MagicMock()
    with patch("pgdrift.commands.shadow_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.shadow_cmd.get_profile", return_value=profile), \
         patch("pgdrift.commands.shadow_cmd.psycopg2.connect", return_value=conn), \
         patch("pgdrift.commands.shadow_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.shadow_cmd.compute_shadow", return_value=report):
        result = cmd_shadow(_args())
    assert result == 1
    out = capsys.readouterr().out
    assert "public.users" in out
