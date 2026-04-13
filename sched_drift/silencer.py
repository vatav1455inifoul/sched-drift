"""Silence/suppress alerts for known drift patterns or maintenance windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from sched_drift.alerts import Alert


@dataclass
class SilenceRule:
    """A rule that suppresses matching alerts."""
    server: Optional[str] = None   # None means match any
    job: Optional[str] = None      # None means match any
    until: Optional[datetime] = None  # None means silence indefinitely
    reason: str = ""

    def matches(self, alert: Alert) -> bool:
        if self.server is not None and alert.server != self.server:
            return False
        if self.job is not None and alert.job != self.job:
            return False
        return True

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if self.until is None:
            return True
        check = now or datetime.utcnow()
        return check <= self.until


def apply_silences(
    alerts: List[Alert],
    rules: List[SilenceRule],
    now: Optional[datetime] = None,
) -> tuple[List[Alert], List[Alert]]:
    """Split alerts into (active, silenced) based on silence rules.

    Returns:
        (active_alerts, silenced_alerts)
    """
    active: List[Alert] = []
    silenced: List[Alert] = []

    active_rules = [r for r in rules if r.is_active(now)]

    for alert in alerts:
        if any(r.matches(alert) for r in active_rules):
            silenced.append(alert)
        else:
            active.append(alert)

    return active, silenced


def format_silenced(silenced: List[Alert]) -> str:
    """Return a human-readable summary of silenced alerts."""
    if not silenced:
        return "No alerts silenced."
    lines = [f"Silenced {len(silenced)} alert(s):"]
    for a in silenced:
        lines.append(f"  [{a.severity.upper()}] {a.server} / {a.job} — {a.message}")
    return "\n".join(lines)
