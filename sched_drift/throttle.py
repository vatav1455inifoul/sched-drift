"""Throttle repeated alerts so the same (server, job, severity) combo
is only surfaced once within a configurable cooldown window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from sched_drift.alerts import Alert


@dataclass
class ThrottleState:
    """Tracks the last time an alert key was emitted."""
    _seen: Dict[Tuple[str, str, str], datetime] = field(default_factory=dict)

    def record(self, key: Tuple[str, str, str], when: datetime) -> None:
        self._seen[key] = when

    def last_seen(self, key: Tuple[str, str, str]) -> datetime | None:
        return self._seen.get(key)


def _alert_key(alert: Alert) -> Tuple[str, str, str]:
    return (alert.server, alert.job, alert.severity)


def throttle_alerts(
    alerts: List[Alert],
    state: ThrottleState,
    cooldown_minutes: int = 60,
    now: datetime | None = None,
) -> List[Alert]:
    """Return only alerts that have not fired within *cooldown_minutes*.

    Side-effect: updates *state* for every alert that passes through.
    """
    if now is None:
        now = datetime.utcnow()
    cooldown = timedelta(minutes=cooldown_minutes)
    passed: List[Alert] = []
    for alert in alerts:
        key = _alert_key(alert)
        last = state.last_seen(key)
        if last is None or (now - last) >= cooldown:
            state.record(key, now)
            passed.append(alert)
    return passed


def format_throttle_summary(
    original: List[Alert],
    passed: List[Alert],
) -> str:
    suppressed = len(original) - len(passed)
    lines = [f"Alerts: {len(passed)} emitted, {suppressed} suppressed by throttle."]
    for alert in passed:
        lines.append(f"  [{alert.severity.upper()}] {alert.server}/{alert.job}: {alert.message}")
    return "\n".join(lines)
