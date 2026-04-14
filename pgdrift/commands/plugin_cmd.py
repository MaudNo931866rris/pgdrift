"""CLI sub-commands for managing and inspecting the pgdrift plugin registry."""

from __future__ import annotations

import argparse

from pgdrift import plugin as _plugin


def cmd_plugin_list(args: argparse.Namespace) -> int:
    """List all currently registered plugins grouped by hook."""
    hooks = _plugin.list_hooks()
    if not hooks:
        print("No plugins registered.")
        return 0
    for hook in sorted(hooks):
        fns = _plugin.get_plugins(hook)
        print(f"[{hook}]")
        for fn in fns:
            module = getattr(fn, "__module__", "?")
            name = getattr(fn, "__name__", repr(fn))
            print(f"  {module}.{name}")
    return 0


def cmd_plugin_load(args: argparse.Namespace) -> int:
    """Discover and load plugins from installed entry points."""
    group = args.group or "pgdrift.plugins"
    count = _plugin.load_entry_points(group=group)
    if count == 0:
        print(f"No plugins found in entry-point group {group!r}.")
    else:
        print(f"Loaded {count} plugin(s) from {group!r}.")
    return 0


def cmd_plugin_clear(args: argparse.Namespace) -> int:
    """Clear all registered plugins (or a specific hook)."""
    hook = args.hook or None
    _plugin.clear(hook=hook)
    if hook:
        print(f"Cleared plugins for hook {hook!r}.")
    else:
        print("Cleared all registered plugins.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("plugin", help="Manage pgdrift plugins")
    sub = p.add_subparsers(dest="plugin_cmd")

    sub.add_parser("list", help="List registered plugins")

    load_p = sub.add_parser("load", help="Load plugins from entry points")
    load_p.add_argument(
        "--group",
        default="pgdrift.plugins",
        help="Entry-point group to scan (default: pgdrift.plugins)",
    )

    clear_p = sub.add_parser("clear", help="Clear registered plugins")
    clear_p.add_argument(
        "--hook",
        default=None,
        help="Only clear this hook (omit to clear all)",
    )

    p.set_defaults(_handler=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    dispatch = {
        "list": cmd_plugin_list,
        "load": cmd_plugin_load,
        "clear": cmd_plugin_clear,
    }
    handler = dispatch.get(args.plugin_cmd)
    if handler is None:
        print("Usage: pgdrift plugin {list,load,clear}")
        return 1
    return handler(args)
