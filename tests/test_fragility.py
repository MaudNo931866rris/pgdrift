import pytest
from pgdrift.inspector import ColumnInfo, TableSchema
from pgdrift.diff import ColumnDiff, TableDiff, DriftReport
from pgdrift.fragility import compute_fragility, FragilityEntry, FragilityReport


def _col(name: str, dtype: str = "text", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name=name, data_type=dtype, is_nullable=nullable)


def _empty_report() -> DriftReport:
    return DriftReport(source="src", target="tgt", table_diffs=[])


def _removed_col_diff(name: str) -> ColumnDiff:
    return ColumnDiff(column=name, change_type="removed", source=_col(name), target=None)


def _type_change_diff(name: str) -> ColumnDiff:
    return ColumnDiff(
        column=name,
        change_type="modified",
        source=_col(name, "integer"),
        target=_col(name, "text"),
    )


def _added_col_diff(name: str) -> ColumnDiff:
    return ColumnDiff(column=name, change_type="added", source=None, target=_col(name))


def test_empty_report_returns_empty_fragility():
    report = compute_fragility(_empty_report())
    assert isinstance(report, FragilityReport)
    assert report.entries == []
    assert not report.any_fragile()


def test_removed_column_increases_score():
    td = TableDiff(table="public.orders", status="modified", column_diffs=[_removed_col_diff("price")])
    report = compute_fragility(DriftReport(source="s", target="t", table_diffs=[td]))
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.has_removals
    assert entry.score >= 2.0


def test_type_change_increases_score():
    td = TableDiff(table="public.users", status="modified", column_diffs=[_type_change_diff("age")])
    report = compute_fragility(DriftReport(source="s", target="t", table_diffs=[td]))
    assert len(report.entries) == 1
    assert report.entries[0].has_type_changes
    assert report.entries[0].score >= 1.5


def test_removed_table_scores_highest():
    td = TableDiff(table="public.legacy", status="removed", column_diffs=[])
    report = compute_fragility(DriftReport(source="s", target="t", table_diffs=[td]))
    assert len(report.entries) == 1
    assert report.entries[0].score >= 5.0


def test_added_column_only_low_score():
    td = TableDiff(table="public.items", status="modified", column_diffs=[_added_col_diff("note")])
    report = compute_fragility(DriftReport(source="s", target="t", table_diffs=[td]))
    # score is only 0.1 per column for additions — still > 0
    assert len(report.entries) == 1
    assert report.entries[0].score < 1.0


def test_most_fragile_returns_top_n():
    tds = [
        TableDiff(table=f"public.t{i}", status="modified", column_diffs=[_removed_col_diff("c")])
        for i in range(6)
    ]
    report = compute_fragility(DriftReport(source="s", target="t", table_diffs=tds))
    top = report.most_fragile(n=3)
    assert len(top) == 3


def test_as_dict_structure():
    td = TableDiff(table="public.orders", status="modified", column_diffs=[_removed_col_diff("price")])
    report = compute_fragility(DriftReport(source="s", target="t", table_diffs=[td]))
    d = report.as_dict()
    assert "entries" in d
    assert "table" in d["entries"][0]
    assert "score" in d["entries"][0]
