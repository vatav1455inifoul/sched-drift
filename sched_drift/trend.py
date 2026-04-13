"""Trend analysis for cron job drift over time."""

from dataclasses import dataclass
from typing import List, Optional
from sched_drift.parser import LogEntry


@dataclass
class TrendResult:
    server: str
    job: str
    slope: float          # seconds of drift change per execution
    direction: str        # 'improving', 'worsening', 'stable'
    sample_count: int
    first_drift: float
    last_drift: float


def _linear_slope(values: List[float]) -> float:
    """Compute slope via simple least-squares linear regression."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _direction(slope: float, threshold: float = 0.5) -> str:
    if slope > threshold:
        return "worsening"
    if slope < -threshold:
        return "improving"
    return "stable"


def analyze_trends(
    entries: List[LogEntry],
    slope_threshold: float = 0.5,
) -> List[TrendResult]:
    """Group entries by (server, job) and compute drift trend for each."""
    groups: dict = {}
    for entry in entries:
        key = (entry.server, entry.job)
        groups.setdefault(key, []).append(entry)

    results: List[TrendResult] = []
    for (server, job), group in sorted(groups.items()):
        sorted_group = sorted(group, key=lambda e: e.actual_time)
        drifts = [e.drift for e in sorted_group]
        slope = _linear_slope(drifts)
        results.append(
            TrendResult(
                server=server,
                job=job,
                slope=round(slope, 3),
                direction=_direction(slope, slope_threshold),
                sample_count=len(drifts),
                first_drift=round(drifts[0], 2),
                last_drift=round(drifts[-1], 2),
            )
        )
    return results


def format_trends(trends: List[TrendResult]) -> str:
    """Return a human-readable trend summary."""
    if not trends:
        return "No trend data available."
    lines = ["Drift Trend Analysis", "=" * 40]
    for t in trends:
        arrow = {"worsening": "↑", "improving": "↓", "stable": "→"}.get(t.direction, "?")
        lines.append(
            f"[{t.server}] {t.job}: {arrow} {t.direction}  "
            f"slope={t.slope:+.3f}s/run  "
            f"n={t.sample_count}  "
            f"first={t.first_drift:+.1f}s  last={t.last_drift:+.1f}s"
        )
    return "\n".join(lines)
