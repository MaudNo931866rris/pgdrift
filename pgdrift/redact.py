"""Redact sensitive column values in schema snapshots before export or display."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Set

REDACTED_MARKER = "<redacted>"

_SENSITIVE_PATTERNS: List[str] = [
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "ssn",
    "credit_card",
    "cvv",
]


def _redact_path(config_dir: Path) -> Path:
    return config_dir / ".pgdrift_redact.json"


def load_redact_rules(config_dir: Path) -> Dict[str, List[str]]:
    """Load redaction rules: {table: [col, ...]}."""
    path = _redact_path(config_dir)
    if not path.exists():
        return {}
    with open(path) as fh:
        return json.load(fh)


def save_redact_rules(config_dir: Path, rules: Dict[str, List[str]]) -> None:
    path = _redact_path(config_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(rules, fh, indent=2)


def add_redact_rule(config_dir: Path, table: str, column: str) -> None:
    rules = load_redact_rules(config_dir)
    cols: List[str] = rules.get(table, [])
    if column not in cols:
        cols.append(column)
    rules[table] = cols
    save_redact_rules(config_dir, rules)


def remove_redact_rule(config_dir: Path, table: str, column: str) -> bool:
    rules = load_redact_rules(config_dir)
    cols = rules.get(table, [])
    if column not in cols:
        return False
    cols.remove(column)
    if cols:
        rules[table] = cols
    else:
        del rules[table]
    save_redact_rules(config_dir, rules)
    return True


def is_sensitive_column(column_name: str) -> bool:
    """Heuristic: return True if the column name matches a known sensitive pattern."""
    lower = column_name.lower()
    return any(pat in lower for pat in _SENSITIVE_PATTERNS)


def should_redact(table: str, column: str, rules: Dict[str, List[str]]) -> bool:
    explicit = column in rules.get(table, [])
    return explicit or is_sensitive_column(column)
