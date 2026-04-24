from __future__ import annotations

import json
import types
from unittest.mock import patch

import pytest

from pgdrift.commands.entropy_cmd import cmd_entropy
from pgdrift.entropy import EntropyReport, EntropyPoint
from pgdrift.trend import TrendPoint


def _args(**kwargs):
    defaults = {"config_dir": ".", "json": False}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


_EMPTY_REPORT = EntropyReport(points=[])


def _non_empty_report():
    return EntropyReport(
        points=[
            EntropyPoint(timestamp="2024-01-01T00:00:00", total_changes=3, entropy=1.58)
        ]
    )


# ---------------------------------------------------------------------------
# no audit records
# ---------------------------------------------------------------------------

def test_no_audit_records_returns_0(capsys):
    with patch("pgdrift.commands.entropy_cmd.audit_mod.load_audit", return_value=[]):
        rc = cmd_entropy(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit records" in out


# ---------------------------------------------------------------------------
# records present but missing 'report' key
# ---------------------------------------------------------------------------

def test_records_without_report_key_returns_0(capsys):
    records = [{"captured_at": "2024-01-01T00:00:00"}]  # no 'report'
    with patch("pgdrift.commands.entropy_cmd.audit_mod.load_audit", return_value=records), \
         patch("pgdrift.commands.entropy_cmd.compute_entropy", return_value=_EMPTY_REPORT):
        rc = cmd_entropy(_args())
    assert rc == 0


# ---------------------------------------------------------------------------
# normal output
# ---------------------------------------------------------------------------

def test_normal_output_returns_0(capsys):
    records = [{"captured_at": "2024-01-01T00:00:00", "report": {}}]
    fake_point = TrendPoint(
        timestamp="2024-01-01T00:00:00",
        added_tables=1,
        removed_tables=1,
        modified_tables=1,
    )
    with patch("pgdrift.commands.entropy_cmd.audit_mod.load_audit", return_value=records), \
         patch("pgdrift.commands.entropy_cmd.trend_mod._point_from_report", return_value=fake_point), \
         patch("pgdrift.commands.entropy_cmd.compute_entropy", return_value=_non_empty_report()):
        rc = cmd_entropy(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "Entropy report" in out


# ---------------------------------------------------------------------------
# --json flag
# ---------------------------------------------------------------------------

def test_json_flag_outputs_json(capsys):
    records = [{"captured_at": "2024-01-01T00:00:00", "report": {}}]
    fake_point = TrendPoint(
        timestamp="2024-01-01T00:00:00",
        added_tables=1,
        removed_tables=0,
        modified_tables=0,
    )
    with patch("pgdrift.commands.entropy_cmd.audit_mod.load_audit", return_value=records), \
         patch("pgdrift.commands.entropy_cmd.trend_mod._point_from_report", return_value=fake_point), \
         patch("pgdrift.commands.entropy_cmd.compute_entropy", return_value=_non_empty_report()):
        rc = cmd_entropy(_args(json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "average_entropy" in data
    assert "points" in data
