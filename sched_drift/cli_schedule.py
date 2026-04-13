"""CLI sub-command: check a cron expression against log entries."""

from __future__ import annotations

import argparse
import sys
from typing import List

from sched_drift.parser import parse_log_file
from sched_drift.schedule import match_schedule


def add_schedule_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "schedule",
        help="Validate log entries against a cron expression and report drift",
    )
    p.add_argument("logfile", help="Path to the log file to analyse")
    p.add_argument("cron", help="Cron expression to validate against (quote it!)")
    p.add_argument(
        "--window",
        type=int,
        default=3600,
        metavar="SECS",
        help="Search window in seconds around each entry (default: 3600)",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        metavar="SECS",
        help="Only show entries where |drift| exceeds this value",
    )
    p.set_defaults(func=run_schedule)


def run_schedule(args: argparse.Namespace) -> int:
    entries = parse_log_file(args.logfile)
    if not entries:
        print(f"No valid log entries found in {args.logfile}", file=sys.stderr)
        return 1

    results = []
    skipped = 0
    for entry in entries:
        match = match_schedule(args.cron, entry.actual_time, window=args.window)
        if match is None:
            skipped += 1
            continue
        if args.threshold is not None and abs(match.drift_seconds) < args.threshold:
            continue
        results.append((entry, match))

    if skipped:
        print(f"Warning: {skipped} entries could not be matched (croniter missing or bad expr)")

    if not results:
        print("No entries exceeded the drift threshold.")
        return 0

    print(f"{'SERVER':<20} {'JOB':<25} {'EXPECTED':<22} {'ACTUAL':<22} {'DRIFT (s)':>10}")
    print("-" * 102)
    for entry, match in results:
        direction = "+" if match.drift_seconds >= 0 else ""
        print(
            f"{entry.server:<20} {entry.job_name:<25} "
            f"{match.expected_time.strftime('%Y-%m-%d %H:%M:%S'):<22} "
            f"{match.actual_time.strftime('%Y-%m-%d %H:%M:%S'):<22} "
            f"{direction}{match.drift_seconds:>9.1f}"
        )

    return 0
