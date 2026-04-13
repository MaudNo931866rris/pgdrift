"""Utilities for persisting and retrieving snapshot history."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List

from pgdrift.snapshot import _table_to_dict, _table_from_dict
from pgdrift.inspector import TableSchema

DEFAULT_HISTORY_DIR = ".pgdrift_history"


def _history_path(directory: str, profile: str, timestamp: str) -> str:
    return os.path.join(directory, f"{profile}_{timestamp}.json")


def save_history(
    tables: List[TableSchema],
    profile: str,
    directory: str = DEFAULT_HISTORY_DIR,
    timestamp: str | None = None,
) -> str:
    """Save a snapshot to the history directory and return the file path."""
    os.makedirs(directory, exist_ok=True)
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = _history_path(directory, profile, timestamp)
    payload: Dict = {
        "profile": profile,
        "captured_at": timestamp,
        "tables": [_table_to_dict(t) for t in tables],
    }
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)
    return path


def load_history(path: str) -> tuple[str, str, List[TableSchema]]:
    """Load a history snapshot; returns (profile, captured_at, tables)."""
    with open(path) as fh:
        payload = json.load(fh)
    profile: str = payload.get("profile", "unknown")
    captured_at: str = payload.get("captured_at", "")
    tables = [_table_from_dict(t) for t in payload.get("tables", [])]
    return profile, captured_at, tables


def list_history(directory: str = DEFAULT_HISTORY_DIR) -> List[str]:
    """Return sorted list of history snapshot file paths."""
    if not os.path.isdir(directory):
        return []
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".json")
    )
