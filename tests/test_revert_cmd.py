import argparse
from unittest.mock import patch, MagicMock
from pgdrift.commands.revert_cmd import cmd_revert
from pgdrift.diff import DriftReport, TableDiff
from pgdrift.revert import RevertPlan, RevertStatement


def _args(**kwargs):
    base = dict(config="pgdrift.yml", source="dev", target="prod")
    base.update(kwargs)
    return argparse.Namespace(**base)


def _make_mock_config(profiles=("dev", "prod")):
    cfg = MagicMock()
    def get_profile(c, name):
        if name in profiles:
            p = MagicMock()
            p.dsn = f"postgresql://localhost/{name}"
            return p
        return None
    return cfg, get_profile


def test_missing_config_returns_1():
    with patch("pgdrift.commands.revert_cmd.load", side_effect=FileNotFoundError):
        assert cmd_revert(_args()) == 1


def test_unknown_source_returns_1():
    cfg, gp = _make_mock_config(profiles=("prod",))
    with patch("pgdrift.commands.revert_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.revert_cmd.get_profile", side_effect=lambda c, n: gp(c, n)):
        assert cmd_revert(_args(source="missing")) == 1


def test_unknown_target_returns_1():
    cfg, gp = _make_mock_config(profiles=("dev",))
    with patch("pgdrift.commands.revert_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.revert_cmd.get_profile", side_effect=lambda c, n: gp(c, n)):
        assert cmd_revert(_args(target="missing")) == 1


def test_no_drift_returns_0(capsys):
    cfg, gp = _make_mock_config()
    empty_report = DriftReport(source="dev", target="prod", table_diffs=[])
    with patch("pgdrift.commands.revert_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.revert_cmd.get_profile", side_effect=lambda c, n: gp(c, n)), \
         patch("pgdrift.commands.revert_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.revert_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.revert_cmd.compute_drift", return_value=empty_report):
        result = cmd_revert(_args())
    assert result == 0
    out = capsys.readouterr().out
    assert "nothing to revert" in out


def test_drift_prints_sql_returns_0(capsys):
    cfg, gp = _make_mock_config()
    td = TableDiff(table="public.foo", status="added", column_diffs=[])
    report = DriftReport(source="dev", target="prod", table_diffs=[td])
    with patch("pgdrift.commands.revert_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.revert_cmd.get_profile", side_effect=lambda c, n: gp(c, n)), \
         patch("pgdrift.commands.revert_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.revert_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.revert_cmd.compute_drift", return_value=report):
        result = cmd_revert(_args())
    assert result == 0
    out = capsys.readouterr().out
    assert "DROP TABLE" in out
