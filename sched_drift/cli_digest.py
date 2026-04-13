"""CLI subcommand: digest — print a ranked drift digest table."""
from __future__ import annotations

import argparse
import sys
from typing import List

from sched_drift.multi_log import load_logs
from sched_drift.reporter import build_report
from sched_drift.digest import build_digest, format_digest


def add_digest_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "digest",
        help="Print a ranked drift digest table for all servers and jobs.",
    )
    p.add_argument(
        "logs",
        nargs="+",
        metavar="LOG",
        help="One or more log file paths to analyse.",
    )
    p.add_argument(
        "--server",
        default=None,
        help="Filter digest to a specific server name.",
    )
    p.add_argument(
        "--warn",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Avg drift threshold for WARN status (default: 60).",
    )
    p.add_argument(
        "--critical",
        type=float,
        default=300.0,
        metavar="SECONDS",
        help="Avg drift threshold for CRITICAL status (default: 300).",
    )
    p.set_defaults(func=run_digest)


def run_digest(args: argparse.Namespace) -> int:
    result = load_logs(args.logs)

    if result.errors:
        for path, err in result.errors.items():
            print(f"[warn] could not load {path}: {err}", file=sys.stderr)

    entries = (
        result.entries_for_server(args.server)
        if args.server
        else result.all_entries
    )

    if not entries:
        print("No log entries found.", file=sys.stderr)
        return 1

    reports = build_report(entries, server=args.server)

    if not reports:
        print("No reports generated.", file=sys.stderr)
        return 1

    digest_lines = build_digest(
        reports,
        warn_threshold=args.warn,
        critical_threshold=args.critical,
    )
    print(format_digest(digest_lines))
    return 0
