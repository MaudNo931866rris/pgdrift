import pytest
from pgdrift.trend import TrendPoint, TrendReport
from pgdrift.anomaly import detect_anomalies, AnomalyReport, _mean, _stddev


def _trend(changes: list) -> TrendReport:
    points = [TrendPoint(label=f"snap{i}", total_changes=c) for i, c in enumerate(changes)]
    return TrendReport(points=points)


def test_empty_trend_returns_empty_report():
    report = detect_anomalies(TrendReport(points=[]))
    assert not report.any_anomalies()


def test_too_few_points_returns_empty():
    report = detect_anomalies(_trend([5, 10]))
    assert not report.any_anomalies()


def test_stable_trend_no_anomalies():
    report = detect_anomalies(_trend([5, 5, 5, 5, 5]))
    assert not report.any_anomalies()


def test_spike_detected_as_anomaly():
    report = detect_anomalies(_trend([2, 2, 2, 50, 2, 2]))
    assert report.any_anomalies()
    labels = [e.snapshot for e in report.entries]
    assert "snap3" in labels


def test_anomaly_entry_fields():
    report = detect_anomalies(_trend([2, 2, 2, 50, 2, 2]))
    entry = next(e for e in report.entries if e.snapshot == "snap3")
    assert entry.changes == 50
    assert entry.z_score > 2.0


def test_as_dict_structure():
    report = detect_anomalies(_trend([2, 2, 2, 50, 2, 2]))
    d = report.as_dict()
    assert "anomalies" in d
    assert isinstance(d["anomalies"], list)
    assert "z_score" in d["anomalies"][0]


def test_mean_helper():
    assert _mean([1, 2, 3, 4, 5]) == 3.0
    assert _mean([]) == 0.0


def test_stddev_helper():
    assert _stddev([2, 4, 4, 4, 5, 5, 7, 9], _mean([2, 4, 4, 4, 5, 5, 7, 9])) == pytest.approx(2.0)
    assert _stddev([1], 1.0) == 0.0


def test_custom_threshold_changes_sensitivity():
    low = detect_anomalies(_trend([2, 2, 2, 10, 2, 2]), threshold=1.0)
    high = detect_anomalies(_trend([2, 2, 2, 10, 2, 2]), threshold=3.0)
    assert len(low.entries) >= len(high.entries)
