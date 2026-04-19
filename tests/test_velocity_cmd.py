"""Tests for pgdrift.commands.velocity_cmd"""
import argparse
from unittest.mock import patch
from pgdrift.commands.velocity_cmd import cmd_velocity
from pgdrift.velocity import VelocityReport, VelocityPoint


def _args(**kwargs):
    defaults = {"snapshot_dir": ".pgdrift/snapshots", "json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _point(captured_at, changes):
    return VelocityPoint(captured_at=captured_at, changes=changes)


def test_no_audit_records_returns_0(capsys):
    with patch("pgdrift.commands.velocity_cmd.compute_velocity", return_value=VelocityReport(points=[])):
        rc = cmd_velocity(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit" in out


def test_with_points_returns_0(capsys):
    report = VelocityReport(points=[
        _point("2024-01-01T00:00:00", 3),
        _point("2024-01-04T00:00:00", 6),
    ])
    with patch("pgdrift.commands.velocity_cmd.compute_velocity", return_value=report):
        rc = cmd_velocity(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "Average" in out


def test_json_flag_outputs_json(capsys):
    report = VelocityReport(points=[
        _point("2024-01-01T00:00:00", 2),
        _point("2024-01-02T00:00:00", 4),
    ])
    with patch("pgdrift.commands.velocity_cmd.compute_velocity", return_value=report):
        rc = cmd_velocity(_args(json=True))
    assert rc == 0
    import json
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "average_per_day" in data
    assert "points" in data
