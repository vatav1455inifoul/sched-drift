"""Alert rules and threshold-based notifications for cron drift."""

from dataclasses import dataclass, field
from typing import List, Optional
from sched_drift.reporter import DriftReport


@dataclass
class AlertRule:
    """Defines a threshold rule for triggering drift alerts."""
    name: str
    max_avg_drift_seconds: Optional[float] = None
    max_single_drift_seconds: Optional[float] = None
    min_late_count: Optional[int] = None


@dataclass
class Alert:
    """Represents a triggered alert."""
    rule_name: str
    server: str
    job: str
    message: str
    severity: str  # "warning" or "critical"


DEFAULT_RULES: List[AlertRule] = [
    AlertRule(
        name="high_avg_drift",
        max_avg_drift_seconds=60.0,
    ),
    AlertRule(
        name="critical_single_drift",
        max_single_drift_seconds=300.0,
    ),
    AlertRule(
        name="frequent_late_runs",
        min_late_count=5,
    ),
]


def evaluate_alerts(
    report: DriftReport,
    rules: Optional[List[AlertRule]] = None,
) -> List[Alert]:
    """Evaluate alert rules against a drift report and return triggered alerts."""
    if rules is None:
        rules = DEFAULT_RULES

    alerts: List[Alert] = []

    for summary in report.summaries:
        for rule in rules:
            if (
                rule.max_avg_drift_seconds is not None
                and abs(summary.avg_drift) > rule.max_avg_drift_seconds
            ):
                alerts.append(Alert(
                    rule_name=rule.name,
                    server=summary.server,
                    job=summary.job,
                    message=(
                        f"Avg drift {summary.avg_drift:.1f}s exceeds "
                        f"threshold {rule.max_avg_drift_seconds}s"
                    ),
                    severity="warning",
                ))

            if (
                rule.max_single_drift_seconds is not None
                and abs(summary.max_drift) > rule.max_single_drift_seconds
            ):
                alerts.append(Alert(
                    rule_name=rule.name,
                    server=summary.server,
                    job=summary.job,
                    message=(
                        f"Max drift {summary.max_drift:.1f}s exceeds "
                        f"threshold {rule.max_single_drift_seconds}s"
                    ),
                    severity="critical",
                ))

            if (
                rule.min_late_count is not None
                and summary.late_count >= rule.min_late_count
            ):
                alerts.append(Alert(
                    rule_name=rule.name,
                    server=summary.server,
                    job=summary.job,
                    message=(
                        f"Job was late {summary.late_count} times "
                        f"(threshold: {rule.min_late_count})"
                    ),
                    severity="warning",
                ))

    return alerts
