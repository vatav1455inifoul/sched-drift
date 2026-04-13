"""Parse and evaluate cron schedules to compute expected execution times."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    from croniter import croniter
except ImportError:  # pragma: no cover
    croniter = None  # type: ignore


@dataclass
class ScheduleMatch:
    """Result of matching a log entry against a cron expression."""

    cron_expr: str
    actual_time: datetime
    expected_time: datetime
    drift_seconds: float

    @property
    def is_late(self) -> bool:
        return self.drift_seconds > 0

    @property
    def is_early(self) -> bool:
        return self.drift_seconds < 0


def nearest_expected(cron_expr: str, actual: datetime, window: int = 3600) -> Optional[datetime]:
    """Return the scheduled time closest to *actual* within *window* seconds.

    Searches one period before and after *actual* to find the nearest tick.
    Returns None if croniter is unavailable or the expression is invalid.
    """
    if croniter is None:
        return None
    try:
        # Start iterator one window before actual so we catch the preceding tick
        start = actual.timestamp() - window
        itr = croniter(cron_expr, datetime.fromtimestamp(start))
        best: Optional[datetime] = None
        best_delta = float("inf")
        for _ in range(20):  # inspect up to 20 upcoming ticks
            tick: datetime = itr.get_next(datetime)
            if tick.timestamp() > actual.timestamp() + window:
                break
            delta = abs((tick - actual).total_seconds())
            if delta < best_delta:
                best_delta = delta
                best = tick
        return best
    except Exception:
        return None


def match_schedule(cron_expr: str, actual: datetime, window: int = 3600) -> Optional[ScheduleMatch]:
    """Match *actual* against *cron_expr* and return a ScheduleMatch or None."""
    expected = nearest_expected(cron_expr, actual, window)
    if expected is None:
        return None
    drift = (actual - expected).total_seconds()
    return ScheduleMatch(
        cron_expr=cron_expr,
        actual_time=actual,
        expected_time=expected,
        drift_seconds=drift,
    )
