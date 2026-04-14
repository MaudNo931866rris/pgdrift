"""Annotation support: attach freeform notes to tables or columns in a profile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

_ANNOTATIONS_DIR = Path(".pgdrift") / "annotations"


def _annotations_path(profile: str) -> Path:
    return _ANNOTATIONS_DIR / f"{profile}.json"


def load_annotations(profile: str) -> Dict[str, str]:
    """Return the annotation mapping for *profile*.

    Keys are ``"table"`` or ``"table.column"`` strings.
    Returns an empty dict when no file exists yet.
    """
    path = _annotations_path(profile)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_annotations(profile: str, annotations: Dict[str, str]) -> None:
    """Persist *annotations* for *profile* to disk."""
    path = _annotations_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(annotations, indent=2))


def add_annotation(profile: str, key: str, note: str) -> None:
    """Add or overwrite the annotation for *key* under *profile*."""
    annotations = load_annotations(profile)
    annotations[key] = note
    save_annotations(profile, annotations)


def remove_annotation(profile: str, key: str) -> bool:
    """Remove the annotation for *key* under *profile*.

    Returns ``True`` when the key existed, ``False`` otherwise.
    """
    annotations = load_annotations(profile)
    if key not in annotations:
        return False
    del annotations[key]
    save_annotations(profile, annotations)
    return True


def get_annotation(profile: str, key: str) -> Optional[str]:
    """Return the note for *key* in *profile*, or ``None`` if absent."""
    return load_annotations(profile).get(key)


def list_annotations(profile: str) -> Dict[str, str]:
    """Alias for :func:`load_annotations` — returns all annotations."""
    return load_annotations(profile)
