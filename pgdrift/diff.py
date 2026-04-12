"""Schema diff logic: compare two schema snapshots and produce a DriftReport."""

from dataclasses import dataclass, field
from pgdrift.inspector import TableSchema, ColumnInfo


@dataclass
class ColumnDiff:
    column: str
    kind: str  # 'added', 'removed', 'changed'
    source: str | None = None
    target: str | None = None


@dataclass
class TableDiff:
    table: str
    kind: str  # 'added', 'removed', 'modified'
    column_diffs: list[ColumnDiff] = field(default_factory=list)


@dataclass
class DriftReport:
    source_profile: str
    target_profile: str
    table_diffs: list[TableDiff] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return len(self.table_diffs) > 0


def _diff_columns(
    source_cols: list[ColumnInfo],
    target_cols: list[ColumnInfo],
) -> list[ColumnDiff]:
    source_map = {c.name: c for c in source_cols}
    target_map = {c.name: c for c in target_cols}
    diffs: list[ColumnDiff] = []

    for name, col in source_map.items():
        if name not in target_map:
            diffs.append(ColumnDiff(column=name, kind="removed", source=col.data_type))
        else:
            t_col = target_map[name]
            if col.data_type != t_col.data_type:
                diffs.append(
                    ColumnDiff(
                        column=name,
                        kind="changed",
                        source=col.data_type,
                        target=t_col.data_type,
                    )
                )

    for name, col in target_map.items():
        if name not in source_map:
            diffs.append(ColumnDiff(column=name, kind="added", target=col.data_type))

    return diffs


def compare_schemas(
    source: dict[str, TableSchema],
    target: dict[str, TableSchema],
    source_profile: str,
    target_profile: str,
) -> DriftReport:
    """Compare two schema dicts and return a DriftReport."""
    report = DriftReport(source_profile=source_profile, target_profile=target_profile)

    for table_name, src_table in source.items():
        if table_name not in target:
            report.table_diffs.append(TableDiff(table=table_name, kind="removed"))
        else:
            col_diffs = _diff_columns(src_table.columns, target[table_name].columns)
            if col_diffs:
                report.table_diffs.append(
                    TableDiff(table=table_name, kind="modified", column_diffs=col_diffs)
                )

    for table_name in target:
        if table_name not in source:
            report.table_diffs.append(TableDiff(table=table_name, kind="added"))

    return report
