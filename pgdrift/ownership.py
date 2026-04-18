"""Track table/column ownership metadata."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _ownership_path(base_dir: str = ".pgdrift") -> Path:
    return Path(base_dir) / "ownership.json"


def load_ownership(base_dir: str = ".pgdrift") -> Dict[str, str]:
    """Return mapping of 'schema.table' or 'schema.table.column' -> owner."""
    path = _ownership_path(base_dir)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def save_ownership(ownership: Dict[str, str], base_dir: str = ".pgdrift") -> None:
    path = _ownership_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(ownership, f, indent=2)


def set_owner(key: str, owner: str, base_dir: str = ".pgdrift") -> None:
    """Set owner for a table or column key."""
    ownership = load_ownership(base_dir)
    ownership[key] = owner
    save_ownership(ownership, base_dir)


def remove_owner(key: str, base_dir: str = ".pgdrift") -> bool:
    ownership = load_ownership(base_dir)
    if key not in ownership:
        return False
    del ownership[key]
    save_ownership(ownership, base_dir)
    return True


def get_owner(key: str, base_dir: str = ".pgdrift") -> Optional[str]:
    return load_ownership(base_dir).get(key)


def list_owners(base_dir: str = ".pgdrift") -> Dict[str, str]:
    return load_ownership(base_dir)
