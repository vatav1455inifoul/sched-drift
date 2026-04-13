"""CLI subcommand: compare two log files for drift window comparison."""
from __future__ import annotations

import argparse
import sys
from typing import List

from sched_drift.compare import compare_windows, format_compare
from sched_drift.parser import parse_log_file
from sched_drift.reporter import build_report


def add_compare_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "compare",
        help="Compare drift between two log windows.",
    )
    p.add_argument("before_log", help="Log file representing the 'before' window.")
    p.add_argument("after_log", help="Log file representing the 'after' window.")
    p.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Minimum delta (seconds) to count as changed (default: 1.0).",
    )
    p.add_argument(
        "--server",
        default=None,
        help="Filter results to a specific server.",
    )
    p.set_defaults(func=run_compare)


def run_compare(args: argparse.Namespace) -> int:
    before_entries = parse_log_file(args.before_log)
    after_entries = parse_log_file(args.after_log)

    if not before_entries and not after_entries:
        print("No log entries found in either file.", file=sys.stderr)
        return 1

    before_reports = build_report(before_entries, server=args.server)
    after_reports = build_report(after_entries, server=args.server)

    results = compare_windows(before_reports, after_reports, threshold=args.threshold)

    if args.server:
        results = [r for r in results if r.server == args.server]

    print(format_compare(results))
    return 0
