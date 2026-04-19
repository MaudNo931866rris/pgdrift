"""Tests for pgdrift.shadow."""
from unittest.mock import patch
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.diff import ColumnDiff, TableDiff
from pgdrift.shadow import ShadowEntry, ShadowReport, compute_shadow


def _col(name, dtype="integer", nullable=False):
    return ColumnInfo(name=name, data_type=dtype, is_nullable=nullable)


def _table(schema, name, cols):
    t = TableSchema(schema=schema, name=name, columns=cols)
    return t


def _make_table_diff(name, added=(), removed=(), modified=()):
    return TableDiff(
        name=name,
        added_columns=list(added),
        removed_columns=list(removed),
        modified_columns=list(modified),
    )


def test_empty_report_when_no_pin():
    with patch("pgdrift.shadow.load_pin_tables", return_value=None):
        report = compute_shadow("missing", {})
    assert not report.any_shadow()
    assert report.entries == []


def test_no_shadow_when_identical():
    t = _table("public", "users", [_col("id")])
    tables = {"public.users": t}
    with patch("pgdrift.shadow.load_pin_tables", return_value=tables), \
         patch("pgdrift.shadow.diff_report") as mock_diff:
        mock_diff.return_value = type("R", (), {"table_diffs": []})() 
        report = compute_shadow("v1", tables)
    assert not report.any_shadow()


def test_shadow_detected_on_added_column():
    added_col = _col("email")
    td = _make_table_diff("public.users", added=[added_col])
    with patch("pgdrift.shadow.load_pin_tables", return_value={}), \
         patch("pgdrift.shadow.diff_report") as mock_diff:
        mock_diff.return_value = type("R", (), {"table_diffs": [td]})()
        report = compute_shadow("v1", {})
    assert report.any_shadow()
    assert len(report.entries) == 1
    assert report.entries[0].table == "public.users"


def test_shadow_skips_clean_table_diffs():
    td = _make_table_diff("public.orders")
    with patch("pgdrift.shadow.load_pin_tables", return_value={}), \
         patch("pgdrift.shadow.diff_report") as mock_diff:
        mock_diff.return_value = type("R", (), {"table_diffs": [td]})()
        report = compute_shadow("v1", {})
    assert not report.any_shadow()


def test_as_dict_structure():
    removed_col = _col("old_field")
    td = _make_table_diff("public.events", removed=[removed_col])
    entry = ShadowEntry(table="public.events", pin_label="v2", drift=td)
    report = ShadowReport(entries=[entry])
    d = report.as_dict()
    assert d["any_shadow"] is True
    assert d["count"] == 1
    assert d["entries"][0]["table"] == "public.events"
    assert "old_field" in d["entries"][0]["removed_columns"]
