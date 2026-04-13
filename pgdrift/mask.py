"""Masking rules: redact or alias sensitive column names in drift output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

_MASK_FILENAME = ".pgdrift_masks.json"


def _mask_path(directory: str = ".") -> Path:
    return Path(directory) / _MASK_FILENAME


def load_masks(directory: str = ".") -> Dict[str, str]:
    """Return mapping of real_column_name -> alias.  Empty dict if no file."""
    path = _mask_path(directory)
    if not path.exists():
        return {}
    with path.open() as fh:
        data = json.load(fh)
    return data.get("masks", {})


def save_masks(masks: Dict[str, str], directory: str = ".") -> None:
    path = _mask_path(directory)
    with path.open("w") as fh:
        json.dump({"masks": masks}, fh, indent=2)


def add_mask(column: str, alias: str, directory: str = ".") -> None:
    masks = load_masks(directory)
    masks[column] = alias
    save_masks(masks, directory)


def remove_mask(column: str, directory: str = ".") -> bool:
    masks = load_masks(directory)
    if column not in masks:
        return False
    del masks[column]
    save_masks(masks, directory)
    return True


def list_masks(directory: str = ".") -> List[Dict[str, str]]:
    masks = load_masks(directory)
    return [{"column": k, "alias": v} for k, v in sorted(masks.items())]


def apply_mask(column_name: str, masks: Dict[str, str]) -> str:
    """Return alias for column_name if one exists, otherwise the original name."""
    return masks.get(column_name, column_name)
