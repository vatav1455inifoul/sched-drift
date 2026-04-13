"""CLI subcommand: correlate drift across servers."""

import argparse
import sys
from typing import List

from sched_drift.multi_log import load_logs
from sched_drift.reporter import build_report
from sched_drift.correlation import correlate, format_correlation


def add_correlation_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "correlate",
        help="Detect systemic vs isolated drift across multiple servers",
    )
    p.add_argument(
        "logs",
        nargs="+",
        metavar="LOG",
        help="Log files to analyse (one per server, or use --dir)",
    )
    p.add_argument(
        "--spread",
        type=float,
        default=30.0,
        metavar="SECONDS",
        help="Max spread (seconds) to still classify drift as systemic (default: 30)",
    )
    p.add_argument(
        "--systemic-only",
        action="store_true",
        default=False,
        help="Only show jobs with systemic drift",
    )
    p.set_defaults(func=run_correlation)


def run_correlation(args: argparse.Namespace) -> int:
    result = load_logs(args.logs)

    if result.errors:
        for path, err in result.errors.items():
            print(f"warning: could not load {path}: {err}", file=sys.stderr)

    if not result.entries:
        print("No log entries found.", file=sys.stderr)
        return 1

    reports = build_report(result.entries)

    if not reports:
        print("No drift reports generated.", file=sys.stderr)
        return 1

    correlation_results = correlate(reports, spread_threshold=args.spread)

    if args.systemic_only:
        correlation_results = [r for r in correlation_results if r.is_systemic]

    print(format_correlation(correlation_results))
    return 0
