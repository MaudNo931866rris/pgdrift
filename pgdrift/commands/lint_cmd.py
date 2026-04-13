"""CLI command for linting a PostgreSQL schema."""

import sys
import argparse
from pgdrift.config import load, get_profile
from pgdrift.inspector import fetch_schema
from pgdrift.lint import lint_tables, LintIssue
import psycopg2


_SEVERITY_COLOR = {
    "error": "\033[31m",
    "warning": "\033[33m",
    "reset": "\033[0m",
}


def _format_issue(issue: LintIssue) -> str:
    color = _SEVERITY_COLOR.get(issue.severity, "")
    reset = _SEVERITY_COLOR["reset"]
    location = f"{issue.table}" + (f".{issue.column}" if issue.column else "")
    return f"{color}[{issue.severity.upper()}]{reset} [{issue.rule}] {location}: {issue.message}"


def cmd_lint(args: argparse.Namespace) -> int:
    try:
        cfg = load(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    profile = get_profile(cfg, args.profile)
    if profile is None:
        print(f"Unknown profile: '{args.profile}'", file=sys.stderr)
        return 1

    try:
        conn = psycopg2.connect(profile.dsn)
        tables = fetch_schema(conn)
        conn.close()
    except Exception as exc:  # pragma: no cover
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    result = lint_tables(tables)

    if not result.has_issues:
        print(f"No lint issues found in profile '{args.profile}'.")
        return 0

    for issue in result.issues:
        print(_format_issue(issue))

    print(
        f"\n{len(result.errors)} error(s), {len(result.warnings)} warning(s) "
        f"in profile '{args.profile}'."
    )
    return 1 if result.errors else 0


def register(subparsers) -> None:
    parser = subparsers.add_parser("lint", help="Lint a schema for common issues")
    parser.add_argument("profile", help="Profile name to lint")
    parser.add_argument(
        "--config", default="pgdrift.yml", help="Path to config file"
    )
    parser.set_defaults(func=cmd_lint)
