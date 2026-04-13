"""Tests for pgdrift.commands.report_cmd."""
from __future__ import annotations

import argparse
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pgdrift.commands.report_cmd import cmd_report
from pgdrift.diff import DriftReport


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        config="pgdrift.yml",
        source="prod",
        target="staging",
        format="markdown",
        output="drift_report.md",
        schema="public",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config():
    profile = MagicMock(host="localhost", port=5432, user="u", password="p", dbname="db")
    conf = MagicMock()
    return conf, profile


def test_missing_config_returns_1(tmp_path):
    args = _args(config=str(tmp_path / "missing.yml"))
    assert cmd_report(args) == 1


def test_unknown_source_profile_returns_1(tmp_path):
    conf, _ = _make_mock_config()
    with patch("pgdrift.commands.report_cmd.cfg.load", return_value=conf), \
         patch("pgdrift.commands.report_cmd.cfg.get_profile", side_effect=KeyError("prod")):
        assert cmd_report(_args()) == 1


def test_report_written_markdown(tmp_path):
    conf, profile = _make_mock_config()
    out_file = tmp_path / "report.md"
    fake_tables: list = []
    report = DriftReport(tables=[])

    with patch("pgdrift.commands.report_cmd.cfg.load", return_value=conf), \
         patch("pgdrift.commands.report_cmd.cfg.get_profile", return_value=profile), \
         patch("pgdrift.commands.report_cmd.cfg.dsn", return_value="postgresql://"), \
         patch("pgdrift.commands.report_cmd.fetch_schema", return_value=fake_tables), \
         patch("pgdrift.commands.report_cmd.compute_drift", return_value=report), \
         patch("psycopg2.connect") as mock_connect:
        mock_connect.return_value.__enter__ = lambda s: MagicMock()
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)
        result = cmd_report(_args(output=str(out_file)))

    assert result == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "pgdrift" in content


def test_report_written_html(tmp_path):
    conf, profile = _make_mock_config()
    out_file = tmp_path / "report.html"
    report = DriftReport(tables=[])

    with patch("pgdrift.commands.report_cmd.cfg.load", return_value=conf), \
         patch("pgdrift.commands.report_cmd.cfg.get_profile", return_value=profile), \
         patch("pgdrift.commands.report_cmd.cfg.dsn", return_value="postgresql://"), \
         patch("pgdrift.commands.report_cmd.fetch_schema", return_value=[]), \
         patch("pgdrift.commands.report_cmd.compute_drift", return_value=report), \
         patch("psycopg2.connect") as mock_connect:
        mock_connect.return_value.__enter__ = lambda s: MagicMock()
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)
        result = cmd_report(_args(format="html", output=str(out_file)))

    assert result == 0
    content = out_file.read_text()
    assert "<!DOCTYPE html>" in content
