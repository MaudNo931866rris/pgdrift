"""Tests for pgdrift.commands.stability_cmd."""
from __future__ import annotations

import argparse
from unittest.mock import patch

from pgdrift.commands.stability_cmd import cmd_stability
from pgdrift.stability import StabilityEntry, StabilityReport, _score


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"snapshot_dir": None, "top": 10, "json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _entry(table: str, changes: int, snapshots: int) -> StabilityEntry:
    return StabilityEntry(
        table=table,
        change_count=changes,
        snapshot_count=snapshots,
        stability_score=_score(changes, snapshots),
    )


def test_no_audit_records_returns_0(capsys):
    empty = StabilityReport()
    with patch("pgdrift.commands.stability_cmd.compute_stability", return_value=empty):
        rc = cmd_stability(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "unavailable" in captured.out


def test_with_entries_returns_0(capsys):
    report = StabilityReport(entries=[
        _entry("public.users", 3, 10),
        _entry("public.orders", 1, 10),
    ])
    with patch("pgdrift.commands.stability_cmd.compute_stability", return_value=report):
        rc = cmd_stability(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "public.users" in captured.out or "public.orders" in captured.out


def test_json_flag_outputs_json(capsys):
    import json
    report = StabilityReport(entries=[_entry("public.t", 2, 5)])
    with patch("pgdrift.commands.stability_cmd.compute_stability", return_value=report):
        rc = cmd_stability(_args(json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert data["entries"][0]["table"] == "public.t"


def test_top_limits_output(capsys):
    entries = [_entry(f"public.t{i}", i, 20) for i in range(1, 15)]
    report = StabilityReport(entries=entries)
    with patch("pgdrift.commands.stability_cmd.compute_stability", return_value=report):
        rc = cmd_stability(_args(top=3))
    assert rc == 0
    out = capsys.readouterr().out
    # Header + separator + 3 data rows = 5 non-empty lines after the first two
    data_lines = [l for l in out.splitlines() if "public.t" in l]
    assert len(data_lines) == 3
