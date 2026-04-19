import argparse
import pytest
from unittest.mock import patch, MagicMock
from pgdrift.commands.anomaly_cmd import cmd_anomaly
from pgdrift.trend import TrendPoint, TrendReport
from pgdrift.anomaly import AnomalyReport, AnomalyEntry


def _args(**kwargs):
    defaults = {
        "profile": "prod",
        "config": "pgdrift.yml",
        "audit_dir": None,
        "threshold": 2.0,
        "json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_config():
    cfg = MagicMock()
    return cfg


def test_missing_config_returns_1():
    with patch("pgdrift.commands.anomaly_cmd.load", return_value=None):
        assert cmd_anomaly(_args()) == 1


def test_no_audit_records_returns_0(capsys):
    with patch("pgdrift.commands.anomaly_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.anomaly_cmd.load_audit", return_value=[]):
        rc = cmd_anomaly(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit" in out


def test_no_anomalies_returns_0(capsys):
    trend = TrendReport(points=[TrendPoint("s1", 5), TrendPoint("s2", 5), TrendPoint("s3", 5)])
    empty = AnomalyReport(entries=[])
    with patch("pgdrift.commands.anomaly_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.anomaly_cmd.load_audit", return_value=[MagicMock()]), \
         patch("pgdrift.commands.anomaly_cmd.build_trend", return_value=trend), \
         patch("pgdrift.commands.anomaly_cmd.detect_anomalies", return_value=empty):
        rc = cmd_anomaly(_args())
    assert rc == 0


def test_anomalies_detected_returns_1(capsys):
    trend = TrendReport(points=[])
    report = AnomalyReport(entries=[AnomalyEntry("snap3", 50, 48, 3.5)])
    with patch("pgdrift.commands.anomaly_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.anomaly_cmd.load_audit", return_value=[MagicMock()]), \
         patch("pgdrift.commands.anomaly_cmd.build_trend", return_value=trend), \
         patch("pgdrift.commands.anomaly_cmd.detect_anomalies", return_value=report):
        rc = cmd_anomaly(_args())
    assert rc == 1
    out = capsys.readouterr().out
    assert "snap3" in out


def test_json_flag_prints_json(capsys):
    trend = TrendReport(points=[])
    report = AnomalyReport(entries=[AnomalyEntry("snap3", 50, 48, 3.5)])
    with patch("pgdrift.commands.anomaly_cmd.load", return_value=_make_mock_config()), \
         patch("pgdrift.commands.anomaly_cmd.load_audit", return_value=[MagicMock()]), \
         patch("pgdrift.commands.anomaly_cmd.build_trend", return_value=trend), \
         patch("pgdrift.commands.anomaly_cmd.detect_anomalies", return_value=report):
        cmd_anomaly(_args(json=True))
    out = capsys.readouterr().out
    assert "anomalies" in out
    assert "z_score" in out
