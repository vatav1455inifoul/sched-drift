"""CLI subcommand: replay — re-score log entries against a new cron expression."""

from __future__ import annotations

import argparse
from typing import List

from sched_drift.multi_log import load_logs
from sched_drift.replay import replay, format_replay


def add_replay_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "replay",
        help="Re-evaluate log entries against a new cron schedule expression.",
    )
    p.add_argument("logs", nargs="+", help="Log file(s) to process.")
    p.add_argument(
        "--expr",
        required=True,
        help="New cron expression to replay against (e.g. '*/5 * * * *').",
    )
    p.add_argument("--server", default=None, help="Filter to a specific server.")
    p.add_argument("--job", default=None, help="Filter to a specific job name.")
    p.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max rows to display (default: 20).",
    )
    p.set_defaults(func=run_replay)


def run_replay(args: argparse.Namespace) -> int:
    result = load_logs(args.logs)
    if result.errors:
        for path, err in result.errors.items():
            print(f"[warn] {path}: {err}")

    entries = list(result.all_entries)
    if not entries:
        print("No log entries found.")
        return 1

    replayed = replay(
        entries,
        new_expr=args.expr,
        server=getattr(args, "server", None),
        job=getattr(args, "job", None),
    )

    if not replayed:
        print("No matching entries after filtering.")
        return 1

    print(format_replay(replayed, limit=args.limit))
    return 0
