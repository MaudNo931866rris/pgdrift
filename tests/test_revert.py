import pytest
from pgdrift.diff import DriftReport, TableDiff, ColumnDiff
from pgdrift.inspector import ColumnInfo
from pgdrift.revert import build_revert_plan, RevertPlan


def _col(name, dtype="integer", nullable=True):
    return ColumnInfo(name=name, data_type=dtype, nullable=nullable)


def test_empty_report_gives_empty_plan():
    report = DriftReport(source="dev", target="prod", table_diffs=[])
    plan = build_revert_plan(report)
    assert plan.is_empty()


def test_added_table_generates_drop():
    td = TableDiff(table="public.orders", status="added", column_diffs=[])
    report = DriftReport(source="dev", target="prod", table_diffs=[td])
    plan = build_revert_plan(report)
    assert len(plan.statements) == 1
    assert "DROP TABLE" in plan.statements[0].sql
    assert "public.orders" in plan.statements[0].sql


def test_removed_table_generates_comment():
    td = TableDiff(table="public.users", status="removed", column_diffs=[])
    report = DriftReport(source="dev", target="prod", table_diffs=[td])
    plan = build_revert_plan(report)
    assert len(plan.statements) == 1
    assert "--" in plan.statements[0].sql


def test_added_column_generates_drop_column():
    cd = ColumnDiff(column="email", status="added", source=None, target=_col("email", "text"))
    td = TableDiff(table="public.users", status="modified", column_diffs=[cd])
    report = DriftReport(source="dev", target="prod", table_diffs=[td])
    plan = build_revert_plan(report)
    assert any("DROP COLUMN" in s.sql for s in plan.statements)


def test_removed_column_generates_add_column():
    cd = ColumnDiff(column="age", status="removed", source=_col("age", "integer", False), target=None)
    td = TableDiff(table="public.users", status="modified", column_diffs=[cd])
    report = DriftReport(source="dev", target="prod", table_diffs=[td])
    plan = build_revert_plan(report)
    stmts = [s.sql for s in plan.statements]
    assert any("ADD COLUMN" in s and "integer" in s for s in stmts)


def test_modified_column_generates_alter_type():
    src_col = _col("price", "numeric")
    tgt_col = _col("price", "text")
    cd = ColumnDiff(column="price", status="modified", source=src_col, target=tgt_col)
    td = TableDiff(table="public.products", status="modified", column_diffs=[cd])
    report = DriftReport(source="dev", target="prod", table_diffs=[td])
    plan = build_revert_plan(report)
    assert any("ALTER COLUMN" in s.sql and "numeric" in s.sql for s in plan.statements)


def test_multiple_diffs_accumulate():
    td1 = TableDiff(table="public.a", status="added", column_diffs=[])
    td2 = TableDiff(table="public.b", status="removed", column_diffs=[])
    report = DriftReport(source="dev", target="prod", table_diffs=[td1, td2])
    plan = build_revert_plan(report)
    assert len(plan.statements) == 2
