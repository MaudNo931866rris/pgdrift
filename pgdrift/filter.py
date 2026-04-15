"""Filter rules for narrowing diff comparisons to specific schemas or table patterns."""

from __future__ import annotations

import fnmatch
import json
import os
from typing import List, Optional

_FILTER_FILE = ".pgdrift_filters.json"


def _filter_path(directory: str = ".") -> str:
    return os.path.join(directory, _FILTER_FILE)


def load_filters(directory: str = ".") -> dict:
    path = _filter_path(directory)
    if not os.path.exists(path):
        return {"schemas": [], "tables": []}
    with open(path) as fh:
        return json.load(fh)


def save_filters(filters: dict, directory: str = ".") -> None:
    path = _filter_path(directory)
    with open(path, "w") as fh:
        json.dump(filters, fh, indent=2)


def add_schema_filter(schema: str, directory: str = ".") -> None:
    filters = load_filters(directory)
    if schema not in filters["schemas"]:
        filters["schemas"].append(schema)
    save_filters(filters, directory)


def add_table_filter(pattern: str, directory: str = ".") -> None:
    filters = load_filters(directory)
    if pattern not in filters["tables"]:
        filters["tables"].append(pattern)
    save_filters(filters, directory)


def remove_filter(value: str, kind: str, directory: str = ".") -> bool:
    filters = load_filters(directory)
    key = "schemas" if kind == "schema" else "tables"
    if value in filters[key]:
        filters[key].remove(value)
        save_filters(filters, directory)
        return True
    return False


def is_table_included(schema: str, table: str, directory: str = ".") -> bool:
    filters = load_filters(directory)
    schema_filters: List[str] = filters.get("schemas", [])
    table_filters: List[str] = filters.get("tables", [])
    if schema_filters and schema not in schema_filters:
        return False
    full = f"{schema}.{table}"
    if table_filters:
        return any(fnmatch.fnmatch(full, p) or fnmatch.fnmatch(table, p) for p in table_filters)
    return True
