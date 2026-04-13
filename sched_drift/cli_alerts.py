"""CLI entry point for the alerts subcommand."""

import sys
import argparse
from typing import List, Optional

from sched_drift.parser import parse_log_file
from sched_drift.reporter import build_report
from sched_drift.alerts import AlertRule, evaluate_alerts, DEFAULT_RULES
from sched_drift.alert_formatter import format_alerts, has_critical


def build_rules_from_args(args: argparse.Namespace) -> List[AlertRule]:
    """Build alert rules from CLI arguments, falling back to defaults."""
    rules = list(DEFAULT_RULES)

    if args.max_avg_drift is not None:
        rules = [r for r in rules if r.name != "high_avg_drift"]
        rules.append(AlertRule(
            name="high_avg_drift",
            max_avg_drift_seconds=args.max_avg_drift,
        ))

    if args.max_single_drift is not None:
        rules = [r for r in rules if r.name != "critical_single_drift"]
        rules.append(AlertRule(
            name="critical_single_drift",
            max_single_drift_seconds=args.max_single_drift,
        ))

    return rules


def run_alerts(argv: Optional[List[str]] = None) -> int:
    """Run the alerts subcommand. Returns exit code."""
    parser = argparse.ArgumentParser(
        prog="sched-drift alerts",
        description="Evaluate alert rules against a cron drift log file.",
    )
    parser.add_argument("logfile", help="Path to the log file to analyse")
    parser.add_argument(
        "--max-avg-drift",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Override max average drift threshold (default: 60s)",
    )
    parser.add_argument(
        "--max-single-drift",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Override max single-run drift threshold (default: 300s)",
    )
    parser.add_argument(
        "--color",
        action="store_true",
        help="Enable colored output",
    )
    parser.add_argument(
        "--server",
        default=None,
        help="Filter alerts to a specific server",
    )

    args = parser.parse_args(argv)

    entries = parse_log_file(args.logfile)
    report = build_report(entries, server_filter=args.server)
    rules = build_rules_from_args(args)
    alerts = evaluate_alerts(report, rules=rules)

    print(format_alerts(alerts, use_color=args.color))

    return 1 if has_critical(alerts) else 0


if __name__ == "__main__":
    sys.exit(run_alerts())
