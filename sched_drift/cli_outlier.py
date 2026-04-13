"""CLI subcommand: outlier — detect drift outliers above a percentile threshold."""
from __future__ import annotations

import argparse
import sys
from typing import List

from sched_drift.multi_log import load_logs
from sched_drift.reporter import build_report
from sched_drift.outlier import detect_outliers, format_outliers


def add_outlier_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "outlier",
        help="Detect log entries whose drift exceeds a percentile threshold.",
    )
    p.add_argument("logs", nargs="+", help="Log file paths to analyse.")
    p.add_argument(
        "--percentile",
        type=float,
        default=95.0,
        metavar="P",
        help="Percentile threshold (default: 95).",
    )
    p.add_argument(
        "--server",
        default=None,
        metavar="NAME",
        help="Filter to a specific server name.",
    )
    p.set_defaults(func=run_outlier)


def run_outlier(args: argparse.Namespace) -> int:
    result = load_logs(args.logs)

    if result.errors:
        for path, err in result.errors.items():
            print(f"Warning: could not load {path}: {err}", file=sys.stderr)

    entries = list(result.all_entries)
    if not entries:
        print("No log entries found.", file=sys.stderr)
        return 1

    reports = [
        build_report(result.entries_for_server(srv))
        for srv in result.servers
        if args.server is None or srv == args.server
    ]
    # flatten: build_report returns a list
    flat_reports = [r for sub in reports for r in sub]

    outliers = detect_outliers(flat_reports, percentile=args.percentile)
    print(format_outliers(outliers, percentile=args.percentile))
    return 0 if outliers else 0
