"""Tests for pgdrift.commands.similarity_cmd."""
import argparse
import types
from unittest.mock import MagicMock, patch
from pgdrift.commands.similarity_cmd import cmd_similarity
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.similarity import SimilarityResult


def _args(**kwargs):
    defaults = dict(source="dev", target="prod", config="pgdrift.yml", json=False, verbose=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config(profiles=("dev", "prod")):
    cfg = MagicMock()
    profile = MagicMock()
    profile.dsn.return_value = "postgresql://localhost/test"
    def get_profile(name):
        if name in profiles:
            return profile
        raise KeyError(name)
    cfg.get_profile.side_effect = get_profile
    return cfg


def _make_table(schema="public", name="users"):
    col = ColumnInfo(name="id", data_type="int", is_nullable=False)
    return TableSchema(schema=schema, name=name, columns=[col])


def test_missing_config_returns_1(tmp_path):
    rc = cmd_similarity(_args(config=str(tmp_path / "missing.yml")))
    assert rc == 1


def test_unknown_source_profile_returns_1(tmp_path):
    cfg = _make_mock_config(profiles=("prod",))
    with patch("pgdrift.commands.similarity_cmd.load", return_value=cfg):
        rc = cmd_similarity(_args())
    assert rc == 1


def test_unknown_target_profile_returns_1(tmp_path):
    cfg = _make_mock_config(profiles=("dev",))
    with patch("pgdrift.commands.similarity_cmd.load", return_value=cfg):
        rc = cmd_similarity(_args())
    assert rc == 1


def test_returns_0_on_success(capsys):
    cfg = _make_mock_config()
    tables = [_make_table()]
    with patch("pgdrift.commands.similarity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.similarity_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.similarity_cmd.fetch_schema", return_value=tables):
        rc = cmd_similarity(_args())
    assert rc == 0


def test_json_flag_outputs_json(capsys):
    cfg = _make_mock_config()
    tables = [_make_table()]
    with patch("pgdrift.commands.similarity_cmd.load", return_value=cfg), \
         patch("pgdrift.commands.similarity_cmd.psycopg2.connect"), \
         patch("pgdrift.commands.similarity_cmd.fetch_schema", return_value=tables):
        cmd_similarity(_args(json=True))
    out = capsys.readouterr().out
    import json
    data = json.loads(out)
    assert "score" in data
