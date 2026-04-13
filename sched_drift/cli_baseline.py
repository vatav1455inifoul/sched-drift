"""CLI sub-commands for baseline management: save and compare."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sched_drift.baseline import (
    compare_baseline,
    format_baseline_diff,
    load_baseline,
    save_baseline,
)
from sched_drift.parser import parse_log_file
from sched_drift.reporter import build_report


DEFAULT_BASELINE = Path(".sched_drift_baseline.json")


def add_baseline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("baseline", help="Save or compare a drift baseline")
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    # save
    save_p = sub.add_parser("save", help="Save current drift averages as baseline")
    save_p.add_argument("logfile", help="Path to the log file")
    save_p.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Where to write the baseline JSON (default: %(default)s)",
    )

    # compare
    cmp_p = sub.add_parser("compare", help="Compare current log against a saved baseline")
    cmp_p.add_argument("logfile", help="Path to the log file")
    cmp_p.add_argument(
        "--baseline", "-b",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON file to compare against (default: %(default)s)",
    )
    cmp_p.add_argument(
        "--min-delta",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Only report changes larger than this many seconds (default: 0)",
    )


def run_baseline(args: argparse.Namespace) -> int:
    """Entry point for the 'baseline' sub-command. Returns an exit code."""
    entries = parse_log_file(args.logfile)
    if not entries:
        print("No valid log entries found.", file=sys.stderr)
        return 1

    reports = build_report(entries)

    if args.baseline_cmd == "save":
        save_baseline(reports, args.output)
        print(f"Baseline saved to {args.output} ({len(reports)} job(s)).")
        return 0

    if args.baseline_cmd == "compare":
        baseline = load_baseline(args.baseline)
        if not baseline:
            print(f"No baseline found at {args.baseline}. Run 'baseline save' first.", file=sys.stderr)
            return 1
        diffs = compare_baseline(reports, baseline, min_delta=args.min_delta)
        print(format_baseline_diff(diffs))
        return 1 if diffs else 0

    print(f"Unknown baseline sub-command: {args.baseline_cmd}", file=sys.stderr)
    return 2
