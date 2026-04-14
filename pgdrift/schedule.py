"""Schedule management for periodic drift checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_SCHEDULE_FILE = ".pgdrift_schedules.json"


def _schedule_path(directory: str = ".") -> Path:
    return Path(directory) / _SCHEDULE_FILE


def load_schedules(directory: str = ".") -> Dict[str, dict]:
    """Load all schedules from disk. Returns empty dict if none exist."""
    path = _schedule_path(directory)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_schedules(schedules: Dict[str, dict], directory: str = ".") -> None:
    """Persist schedules to disk."""
    path = _schedule_path(directory)
    with open(path, "w") as f:
        json.dump(schedules, f, indent=2)


def add_schedule(
    name: str,
    source: str,
    target: str,
    interval_minutes: int,
    directory: str = ".",
) -> dict:
    """Add or overwrite a named schedule entry."""
    schedules = load_schedules(directory)
    entry = {
        "name": name,
        "source": source,
        "target": target,
        "interval_minutes": interval_minutes,
    }
    schedules[name] = entry
    save_schedules(schedules, directory)
    return entry


def remove_schedule(name: str, directory: str = ".") -> bool:
    """Remove a schedule by name. Returns True if it existed."""
    schedules = load_schedules(directory)
    if name not in schedules:
        return False
    del schedules[name]
    save_schedules(schedules, directory)
    return True


def get_schedule(name: str, directory: str = ".") -> Optional[dict]:
    """Return a single schedule entry or None."""
    return load_schedules(directory).get(name)


def list_schedules(directory: str = ".") -> List[dict]:
    """Return all schedule entries as a list."""
    return list(load_schedules(directory).values())
