from __future__ import annotations
import argparse
import json
from pgdrift.config import load
from pgdrift.audit import load_audit
from pgdrift.trend import build_trend
from pgdrift.anomaly import detect_anomalies


def cmd_anomaly(args: argparse.Namespace) -> int:
    cfg = load(args.config)
    if cfg is None:
        print("Error: config file not found.")
        return 1

    records = load_audit(args.profile, base_dir=args.audit_dir)
    if not records:
        print("No audit records found.")
        return 0

    trend = build_trend(records)
    threshold = getattr(args, "threshold", 2.0)
    report = detect_anomalies(trend, threshold=threshold)

    if not report.any_anomalies():
        print("No anomalies detected.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(f"Anomalies detected ({len(report.entries)}):")
        for e in report.entries:
            print(f"  {e.snapshot}: {e.changes} changes (z={e.z_score:.2f}, delta={e.delta:+d})")

    return 1


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("anomaly", help="Detect anomalous drift spikes in audit history")
    p.add_argument("profile", help="Profile name")
    p.add_argument("--config", default="pgdrift.yml")
    p.add_argument("--audit-dir", default=None)
    p.add_argument("--threshold", type=float, default=2.0, help="Z-score threshold")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_anomaly)
