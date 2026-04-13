"""CLI sub-command: window — filter entries by time range and report drift."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import List, Optional

from sched_drift.multi_log import load_logs
from sched_drift.reporter import build_report, format_report
from sched_drift.window_filter import (
    WindowFilter,
    filter_reports,
    format_window_summary,
)


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string; attach UTC if no tzinfo."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def add_window_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "window",
        help="Filter log entries by time window and report drift",
    )
    p.add_argument("logs", nargs="+", help="Log file paths")
    p.add_argument("--start", default=None, help="Window start (ISO-8601)")
    p.add_argument("--end", default=None, help="Window end (ISO-8601)")
    p.add_argument("--server", default=None, help="Filter by server name")
    p.set_defaults(func=run_window)


def run_window(args: argparse.Namespace) -> int:
    result = load_logs(args.logs)

    if result.errors:
        for path, err in result.errors.items():
            print(f"[warn] {path}: {err}")

    entries = result.all_entries
    if not entries:
        print("No entries found.")
        return 1

    start: Optional[datetime] = _parse_dt(args.start) if args.start else None
    end: Optional[datetime] = _parse_dt(args.end) if args.end else None
    wf = WindowFilter(start=start, end=end)

    reports = build_report(entries, server=getattr(args, "server", None))
    filtered = filter_reports(reports, wf)

    if not filtered:
        print("No entries match the specified window.")
        return 1

    print(format_window_summary(filtered, wf))
    print()
    print(format_report(filtered))
    return 0
