"""CLI integration for alert throttling.

Usage (as a sub-command of the main CLI):
    sched-drift throttle --log path/to/server.log --cooldown 30
"""

from __future__ import annotations

import argparse
from datetime import datetime

from sched_drift.alerts import AlertRule, evaluate_alerts
from sched_drift.cli_alerts import build_rules_from_args
from sched_drift.multi_log import load_logs
from sched_drift.reporter import build_report
from sched_drift.throttle import ThrottleState, format_throttle_summary, throttle_alerts

# Module-level state so repeated CLI invocations within the same process
# (e.g. tests or long-running wrappers) accumulate history.
_GLOBAL_STATE: ThrottleState = ThrottleState()


def add_throttle_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "throttle",
        help="Evaluate alerts with cooldown-based throttling.",
    )
    p.add_argument("logs", nargs="+", help="Log file(s) to analyse.")
    p.add_argument(
        "--cooldown",
        type=int,
        default=60,
        metavar="MINUTES",
        help="Suppress repeated alerts within this window (default: 60).",
    )
    p.add_argument("--warn-avg", type=float, default=30.0)
    p.add_argument("--crit-avg", type=float, default=120.0)
    p.add_argument("--warn-single", type=float, default=60.0)
    p.add_argument("--crit-single", type=float, default=300.0)
    p.add_argument("--reset", action="store_true", help="Reset throttle state before running.")
    p.set_defaults(func=run_throttle)


def run_throttle(args: argparse.Namespace) -> int:
    global _GLOBAL_STATE

    if args.reset:
        _GLOBAL_STATE = ThrottleState()

    result = load_logs(args.logs)
    if not result.entries:
        print("No log entries found.")
        return 1

    reports = build_report(result.entries)
    rules: list[AlertRule] = build_rules_from_args(args)
    alerts = evaluate_alerts(reports, rules)

    passed = throttle_alerts(
        alerts,
        _GLOBAL_STATE,
        cooldown_minutes=args.cooldown,
        now=datetime.utcnow(),
    )

    print(format_throttle_summary(alerts, passed))
    return 0 if not passed else 2
