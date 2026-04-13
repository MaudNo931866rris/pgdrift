"""Formats DriftReport output for CLI display."""

from dataclasses import dataclass
from typing import IO
import sys

from pgdrift.diff import DriftReport, TableDiff, ColumnDiff


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def _format_column_diff(diff: ColumnDiff, use_color: bool) -> list[str]:
    lines = []
    if diff.status == "added":
        lines.append(
            _colorize(f"    + column '{diff.name}' added ({diff.target_type})", ANSI_GREEN, use_color)
        )
    elif diff.status == "removed":
        lines.append(
            _colorize(f"    - column '{diff.name}' removed ({diff.source_type})", ANSI_RED, use_color)
        )
    elif diff.status == "changed":
        lines.append(
            _colorize(
                f"    ~ column '{diff.name}' changed: {diff.source_type} -> {diff.target_type}",
                ANSI_YELLOW,
                use_color,
            )
        )
    return lines


def _format_table_diff(diff: TableDiff, use_color: bool) -> list[str]:
    lines = []
    if diff.status == "added":
        prefix = _colorize("+", ANSI_GREEN, use_color)
        lines.append(f"  {prefix} table '{diff.table_name}' added")
    elif diff.status == "removed":
        prefix = _colorize("-", ANSI_RED, use_color)
        lines.append(f"  {prefix} table '{diff.table_name}' removed")
    elif diff.status == "changed":
        prefix = _colorize("~", ANSI_YELLOW, use_color)
        lines.append(f"  {prefix} table '{diff.table_name}' changed:")
        for col_diff in diff.column_diffs:
            lines.extend(_format_column_diff(col_diff, use_color))
    return lines


def format_report(report: DriftReport, use_color: bool = True, stream: IO = None) -> str:
    """Format a DriftReport as a human-readable string."""
    if stream is None:
        stream = sys.stdout

    lines = []
    header = _colorize("Schema Drift Report", ANSI_BOLD, use_color)
    lines.append(header)
    lines.append(f"  Source: {report.source_env}  ->  Target: {report.target_env}")
    lines.append("")

    if not report.has_drift():
        lines.append(_colorize("  No drift detected.", ANSI_GREEN, use_color))
    else:
        for table_diff in report.table_diffs:
            lines.extend(_format_table_diff(table_diff, use_color))

    lines.append("")
    output = "\n".join(lines)
    return output
