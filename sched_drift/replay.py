"""Replay module: re-evaluate past log entries against a new cron schedule."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sched_drift.parser import LogEntry
from sched_drift.schedule import match_schedule, ScheduleMatch


@dataclass
class ReplayResult:
    entry: LogEntry
    original_drift: float
    replayed: Optional[ScheduleMatch]
    delta: Optional[float]  # replayed.drift_seconds - original_drift

    @property
    def improved(self) -> Optional[bool]:
        """True if the new schedule reduces absolute drift."""
        if self.delta is None:
            return None
        return abs(self.replayed.drift_seconds) < abs(self.original_drift)  # type: ignore[union-attr]


def replay(
    entries: List[LogEntry],
    new_expr: str,
    server: Optional[str] = None,
    job: Optional[str] = None,
) -> List[ReplayResult]:
    """Re-evaluate *entries* against *new_expr*, optionally filtering by server/job."""
    results: List[ReplayResult] = []
    for entry in entries:
        if server and entry.server != server:
            continue
        if job and entry.job != job:
            continue
        match = match_schedule(entry.actual_time, new_expr)
        delta: Optional[float] = None
        if match is not None:
            delta = match.drift_seconds - entry.drift_seconds
        results.append(
            ReplayResult(
                entry=entry,
                original_drift=entry.drift_seconds,
                replayed=match,
                delta=delta,
            )
        )
    return results


def format_replay(results: List[ReplayResult], limit: int = 20) -> str:
    if not results:
        return "No replay results."
    lines = [f"{'SERVER':<16} {'JOB':<20} {'ORIG':>8} {'NEW':>8} {'DELTA':>8} IMP"]
    lines.append("-" * 68)
    for r in results[:limit]:
        new_d = f"{r.replayed.drift_seconds:+.1f}" if r.replayed else "N/A"
        delta = f"{r.delta:+.1f}" if r.delta is not None else "N/A"
        imp = ("yes" if r.improved else "no") if r.improved is not None else "-"
        lines.append(
            f"{r.entry.server:<16} {r.entry.job:<20}"
            f" {r.original_drift:>+8.1f} {new_d:>8} {delta:>8} {imp}"
        )
    return "\n".join(lines)
