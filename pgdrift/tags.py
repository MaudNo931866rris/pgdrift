"""Tag management for pgdrift snapshots and baselines."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

_TAGS_FILE = ".pgdrift_tags.json"


def _tags_path(directory: str = ".") -> Path:
    return Path(directory) / _TAGS_FILE


def load_tags(directory: str = ".") -> Dict[str, str]:
    """Load the tag-to-filename mapping from disk."""
    path = _tags_path(directory)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Tags file '{path}' is corrupted or invalid JSON: {e}"
            ) from e


def save_tags(tags: Dict[str, str], directory: str = ".") -> None:
    """Persist the tag-to-filename mapping to disk."""
    path = _tags_path(directory)
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(tags, f, indent=2)


def add_tag(tag: str, filename: str, directory: str = ".") -> None:
    """Associate a tag with a snapshot or baseline filename."""
    tags = load_tags(directory)
    tags[tag] = filename
    save_tags(tags, directory)


def remove_tag(tag: str, directory: str = ".") -> bool:
    """Remove a tag. Returns True if removed, False if not found."""
    tags = load_tags(directory)
    if tag not in tags:
        return False
    del tags[tag]
    save_tags(tags, directory)
    return True


def resolve_tag(tag: str, directory: str = ".") -> Optional[str]:
    """Resolve a tag to its associated filename, or None if not found."""
    return load_tags(directory).get(tag)


def list_tags(directory: str = ".") -> List[Dict[str, str]]:
    """Return a list of dicts with 'tag' and 'filename' keys."""
    tags = load_tags(directory)
    return [{"tag": t, "filename": f} for t, f in sorted(tags.items())]
