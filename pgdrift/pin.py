"""Pin a schema state to detect future deviations from a known-good baseline."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pgdrift.inspector import TableSchema
from pgdrift.snapshot import _table_to_dict, _table_from_dict


def _pin_path(profile: str, pin_dir: str = ".pgdrift/pins") -> Path:
    return Path(pin_dir) / f"{profile}.json"


def save_pin(profile: str, tables: List[TableSchema], pin_dir: str = ".pgdrift/pins") -> Path:
    path = _pin_path(profile, pin_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile": profile,
        "pinned_at": datetime.now(timezone.utc).isoformat(),
        "tables": [_table_to_dict(t) for t in tables],
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_pin(profile: str, pin_dir: str = ".pgdrift/pins") -> Optional[Dict]:
    path = _pin_path(profile, pin_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_pin_tables(profile: str, pin_dir: str = ".pgdrift/pins") -> Optional[List[TableSchema]]:
    data = load_pin(profile, pin_dir)
    if data is None:
        return None
    return [_table_from_dict(t) for t in data["tables"]]


def delete_pin(profile: str, pin_dir: str = ".pgdrift/pins") -> bool:
    path = _pin_path(profile, pin_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def list_pins(pin_dir: str = ".pgdrift/pins") -> List[str]:
    base = Path(pin_dir)
    if not base.exists():
        return []
    return [p.stem for p in sorted(base.glob("*.json"))]
