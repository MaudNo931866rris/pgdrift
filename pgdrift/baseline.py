"""Baseline management: mark a drift report as acknowledged/accepted."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_BASELINE_DIR = Path(".pgdrift") / "baselines"


def _baseline_path(name: str, base_dir: Path = DEFAULT_BASELINE_DIR) -> Path:
    return base_dir / f"{name}.json"


def save_baseline(
    name: str,
    table_names: List[str],
    note: Optional[str] = None,
    base_dir: Path = DEFAULT_BASELINE_DIR,
) -> Path:
    """Persist a baseline entry recording which tables are acknowledged."""
    base_dir.mkdir(parents=True, exist_ok=True)
    path = _baseline_path(name, base_dir)
    payload = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": note or "",
        "acknowledged_tables": sorted(table_names),
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_baseline(
    name: str, base_dir: Path = DEFAULT_BASELINE_DIR
) -> Optional[Dict]:
    """Load a baseline by name; returns None if not found."""
    path = _baseline_path(name, base_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_baselines(base_dir: Path = DEFAULT_BASELINE_DIR) -> List[str]:
    """Return sorted list of baseline names stored on disk."""
    if not base_dir.exists():
        return []
    return sorted(
        p.stem for p in base_dir.glob("*.json")
    )


def delete_baseline(
    name: str, base_dir: Path = DEFAULT_BASELINE_DIR
) -> bool:
    """Delete a baseline file; returns True if deleted, False if not found."""
    path = _baseline_path(name, base_dir)
    if path.exists():
        path.unlink()
        return True
    return False
