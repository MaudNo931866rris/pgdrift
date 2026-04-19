"""CLI command for hotspot analysis."""
from __future__ import annotations
import argparse
import json
from pgdrift.config import load
from pgdrift.hotspot import compute_hotspots, most_changed, as_dict


def cmd_hotspot(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        return 1

    profile = getattr(args, "profile", None)
    if profile and profile not in [p.name for p in cfg.profiles]:
        print(f"Unknown profile: {profile}")
        return 1

    profile_name = profile or (cfg.profiles[0].name if cfg.profiles else "default")
    report = compute_hotspots(profile_name, getattr(args, "snapshots_dir", "."))
    top = most_changed(report, n=getattr(args, "top", 10))

    if not top:
        print("No hotspot data found.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(as_dict(report), indent=2))
    else:
        print(f"Top hotspots for profile '{profile_name}':")
        for e in top:
            print(f"  {e.table}: {e.change_count} change(s)")
            for col, cnt in sorted(e.column_changes.items(), key=lambda x: -x[1]):
                print(f"    {col}: {cnt}")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("hotspot", help="Show most frequently changed tables")
    p.add_argument("--profile", default=None)
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--json", action="store_true")
    p.add_argument("--snapshots-dir", dest="snapshots_dir", default=".")
    p.set_defaults(func=cmd_hotspot)
