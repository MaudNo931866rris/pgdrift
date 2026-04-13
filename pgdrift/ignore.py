"""Support for ignoring specific tables or columns during drift detection."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import List, Optional

_IGNORE_FILE = ".pgdrift_ignore"


def _ignore_path(directory: str = ".") -> Path:
    return Path(directory) / _IGNORE_FILE


def load_ignore(directory: str = ".") -> dict:
    """Load ignore rules from .pgdrift_ignore in the given directory."""
    path = _ignore_path(directory)
    if not path.exists():
        return {"tables": [], "columns": []}
    with path.open() as fh:
        data = json.load(fh)
    data.setdefault("tables", [])
    data.setdefault("columns", [])
    return data


def save_ignore(rules: dict, directory: str = ".") -> None:
    """Persist ignore rules to .pgdrift_ignore."""
    path = _ignore_path(directory)
    with path.open("w") as fh:
        json.dump(rules, fh, indent=2)


def is_table_ignored(full_name: str, rules: dict) -> bool:
    """Return True if *full_name* (schema.table) matches any table ignore pattern."""
    for pattern in rules.get("tables", []):
        if fnmatch.fnmatch(full_name, pattern):
            return True
    return False


def is_column_ignored(full_name: str, column_name: str, rules: dict) -> bool:
    """Return True if *column_name* in *full_name* matches any column ignore pattern.

    Column patterns are expressed as ``schema.table.column`` globs.
    """
    for pattern in rules.get("columns", []):
        qualified = f"{full_name}.{column_name}"
        if fnmatch.fnmatch(qualified, pattern):
            return True
    return False


def add_table_rule(pattern: str, directory: str = ".") -> None:
    rules = load_ignore(directory)
    if pattern not in rules["tables"]:
        rules["tables"].append(pattern)
    save_ignore(rules, directory)


def add_column_rule(pattern: str, directory: str = ".") -> None:
    rules = load_ignore(directory)
    if pattern not in rules["columns"]:
        rules["columns"].append(pattern)
    save_ignore(rules, directory)


def remove_rule(pattern: str, directory: str = ".") -> bool:
    """Remove *pattern* from either tables or columns list. Returns True if found."""
    rules = load_ignore(directory)
    for key in ("tables", "columns"):
        if pattern in rules[key]:
            rules[key].remove(pattern)
            save_ignore(rules, directory)
            return True
    return False
