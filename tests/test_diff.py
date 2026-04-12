"""Unit tests for pgdrift.diff schema comparison logic."""

import pytest
from pgdrift.inspector import TableSchema, ColumnInfo
from pgdrift.diff import compare_schemas, DriftReport


def make_table(full_name: str, columns: list[tuple]) -> TableSchema:
    schema, name = full_name.split(".")
    cols = [
        ColumnInfo(name=c[0], data_type=c[1], is_nullable=c[2])
        for c in columns
    ]
    return TableSchema(name=name, schema=schema, columns=cols)


@pytest.fixture
def base_source():
    return {
        "public.users": make_table(
            "public.users",
            [("id", "integer", False), ("email", "character varying", False)],
        ),
        "public.orders": make_table(
            "public.orders",
            [("id", "integer", False), ("total", "numeric", False)],
        ),
    }


def test_no_drift_when_identical(base_source):
    report = compare_schemas(base_source, base_source, "dev", "staging")
    assert not report.has_drift
    assert report.source_profile == "dev"
    assert report.target_profile == "staging"


def test_detects_added_table(base_source):
    target = dict(base_source)
    target["public.products"] = make_table(
        "public.products", [("id", "integer", False)]
    )
    report = compare_schemas(base_source, target, "dev", "prod")
    assert report.has_drift
    added = [d for d in report.table_diffs if d.kind == "added"]
    assert any(d.table == "public.products" for d in added)


def test_detects_removed_table(base_source):
    target = {k: v for k, v in base_source.items() if k != "public.orders"}
    report = compare_schemas(base_source, target, "dev", "prod")
    removed = [d for d in report.table_diffs if d.kind == "removed"]
    assert any(d.table == "public.orders" for d in removed)


def test_detects_changed_column_type(base_source):
    target = dict(base_source)
    target["public.users"] = make_table(
        "public.users",
        [("id", "bigint", False), ("email", "character varying", False)],
    )
    report = compare_schemas(base_source, target, "dev", "prod")
    modified = [d for d in report.table_diffs if d.kind == "modified"]
    assert len(modified) == 1
    col_diff = modified[0].column_diffs[0]
    assert col_diff.column == "id"
    assert col_diff.source == "integer"
    assert col_diff.target == "bigint"


def test_detects_added_column(base_source):
    target = dict(base_source)
    target["public.users"] = make_table(
        "public.users",
        [
            ("id", "integer", False),
            ("email", "character varying", False),
            ("created_at", "timestamp", True),
        ],
    )
    report = compare_schemas(base_source, target, "dev", "prod")
    modified = [d for d in report.table_diffs if d.kind == "modified"]
    added_cols = [c for c in modified[0].column_diffs if c.kind == "added"]
    assert any(c.column == "created_at" for c in added_cols)
