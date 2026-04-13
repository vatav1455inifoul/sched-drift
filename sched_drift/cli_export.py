"""CLI subcommand for exporting drift reports to JSON or CSV."""

import argparse
import sys
from typing import List

from sched_drift.parser import parse_log_file
from sched_drift.reporter import build_report
from sched_drift.exporter import export_json, export_csv


def add_export_subparser(subparsers) -> None:
    """Register the 'export' subcommand onto an existing subparsers object."""
    parser = subparsers.add_parser(
        "export",
        help="Export drift report to JSON or CSV",
    )
    parser.add_argument("logfile", help="Path to the cron log file")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        dest="fmt",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--server",
        default=None,
        help="Filter results to a specific server",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write output to a file instead of stdout",
    )


def run_export(args: argparse.Namespace) -> int:
    """Execute the export subcommand. Returns an exit code."""
    entries = parse_log_file(args.logfile)
    if not entries:
        print("No valid log entries found.", file=sys.stderr)
        return 1

    reports = build_report(entries, server_filter=getattr(args, "server", None))
    if not reports:
        print("No reports generated (check --server filter).", file=sys.stderr)
        return 1

    if args.fmt == "csv":
        output = export_csv(reports)
    else:
        output = export_json(reports)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Exported {len(reports)} report(s) to {args.output}")
    else:
        print(output)

    return 0
