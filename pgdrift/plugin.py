"""Plugin registry for pgdrift — allows external packages to register
custom formatters, linters, or exporters via entry points or direct
registration."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

# Registry maps hook names to lists of callables.
_REGISTRY: Dict[str, List[Callable]] = {}

VALID_HOOKS = frozenset([
    "formatter",
    "linter",
    "exporter",
    "notifier",
])


def register(hook: str, fn: Callable) -> None:
    """Register *fn* under the given *hook* name.

    Raises ValueError if the hook name is not recognised.
    """
    if hook not in VALID_HOOKS:
        raise ValueError(
            f"Unknown hook {hook!r}. Valid hooks: {sorted(VALID_HOOKS)}"
        )
    _REGISTRY.setdefault(hook, []).append(fn)


def get_plugins(hook: str) -> List[Callable]:
    """Return all callables registered under *hook* (may be empty)."""
    return list(_REGISTRY.get(hook, []))


def clear(hook: Optional[str] = None) -> None:
    """Clear registered plugins.  Pass a hook name to clear only that hook,
    or omit to clear everything (useful in tests)."""
    if hook is None:
        _REGISTRY.clear()
    else:
        _REGISTRY.pop(hook, None)


def list_hooks() -> List[str]:
    """Return the names of hooks that currently have at least one plugin."""
    return [h for h, fns in _REGISTRY.items() if fns]


def load_entry_points(group: str = "pgdrift.plugins") -> int:
    """Discover and load plugins advertised via *importlib.metadata* entry
    points in *group*.  Returns the number of plugins loaded."""
    try:
        from importlib.metadata import entry_points  # Python 3.9+
        eps = entry_points(group=group)
    except TypeError:
        # Python 3.8 fallback
        from importlib.metadata import entry_points as _ep
        eps = _ep().get(group, [])

    loaded = 0
    for ep in eps:
        try:
            fn = ep.load()
            hook = ep.name.split(".")[0]
            register(hook, fn)
            loaded += 1
        except Exception:
            pass
    return loaded
