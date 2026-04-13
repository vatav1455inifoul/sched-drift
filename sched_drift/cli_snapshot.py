"""CLI subcommands for snapshot capture and diff."""

from __future__ import annotations

import argparse
import sys
from typing import List

from sched_drift.multi_log import load_logs
from sched_drift.reporter import build_report
from sched_drift.snapshot import (
    capture_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
    format_snapshot_diff,
)


def add_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("snapshot", help="Capture or diff drift snapshots")
    sub = p.add_subparsers(dest="snapshot_cmd", required=True)

    # capture sub-command
    cap = sub.add_parser("capture", help="Save current drift state to a snapshot file")
    cap.add_argument("logs", nargs="+", help="Log files to analyse")
    cap.add_argument("--out", default="snapshot.json", help="Output snapshot file")

    # diff sub-command
    dif = sub.add_parser("diff", help="Compare two snapshot files")
    dif.add_argument("before", help="Baseline snapshot file")
    dif.add_argument("after", help="Current snapshot file")


def run_snapshot(args: argparse.Namespace) -> int:
    if args.snapshot_cmd == "capture":
        return _run_capture(args)
    if args.snapshot_cmd == "diff":
        return _run_diff(args)
    return 1


def _run_capture(args: argparse.Namespace) -> int:
    result = load_logs(args.logs)
    if not result.entries:
        print("No log entries found.", file=sys.stderr)
        return 1
    reports = build_report(result.entries)
    entries = capture_snapshot(reports)
    save_snapshot(entries, args.out)
    print(f"Snapshot saved to {args.out} ({len(entries)} entries).")
    return 0


def _run_diff(args: argparse.Namespace) -> int:
    before = load_snapshot(args.before)
    after = load_snapshot(args.after)
    if not before:
        print(f"Could not load baseline snapshot: {args.before}", file=sys.stderr)
        return 1
    if not after:
        print(f"Could not load current snapshot: {args.after}", file=sys.stderr)
        return 1
    diffs = diff_snapshots(before, after)
    print(format_snapshot_diff(diffs))
    return 0
