"""Snapshot support: save and load schema snapshots to/from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from pgdrift.inspector import ColumnInfo, TableSchema


def _table_to_dict(table: TableSchema) -> dict:
    return {
        "schema": table.schema,
        "name": table.name,
        "columns": [
            {
                "name": col.name,
                "data_type": col.data_type,
                "nullable": col.nullable,
                "default": col.default,
            }
            for col in table.columns
        ],
    }


def _table_from_dict(data: dict) -> TableSchema:
    columns = [
        ColumnInfo(
            name=c["name"],
            data_type=c["data_type"],
            nullable=c["nullable"],
            default=c["default"],
        )
        for c in data["columns"]
    ]
    return TableSchema(schema=data["schema"], name=data["name"], columns=columns)


def save_snapshot(tables: Dict[str, TableSchema], path: Path) -> None:
    """Serialize a schema dict to a JSON snapshot file."""
    payload = {key: _table_to_dict(tbl) for key, tbl in tables.items()}
    path.write_text(json.dumps(payload, indent=2))


def load_snapshot(path: Path) -> Dict[str, TableSchema]:
    """Deserialize a JSON snapshot file into a schema dict."""
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    raw = json.loads(path.read_text())
    return {key: _table_from_dict(val) for key, val in raw.items()}
