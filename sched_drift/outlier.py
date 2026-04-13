"""Outlier detection: flag entries whose drift exceeds a percentile threshold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport


@dataclass
class OutlierEntry:
    server: str
    job: str
    drift_seconds: float
    percentile: float  # e.g. 95.0
    threshold_seconds: float

    def __str__(self) -> str:
        direction = "late" if self.drift_seconds > 0 else "early"
        return (
            f"[{self.server}] {self.job}: drift {self.drift_seconds:+.1f}s "
            f"({direction}, p{self.percentile:.0f} threshold ±{self.threshold_seconds:.1f}s)"
        )


def _percentile(values: List[float], p: float) -> float:
    """Return the p-th percentile of *values* (0–100). Simple nearest-rank."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = max(0, int(len(sorted_vals) * p / 100) - 1)
    return sorted_vals[idx]


def detect_outliers(
    reports: List[DriftReport],
    percentile: float = 95.0,
) -> List[OutlierEntry]:
    """Return entries whose |drift| exceeds the given percentile across all entries."""
    all_abs: List[float] = []
    for r in reports:
        all_abs.extend(abs(e.drift_seconds) for e in r.entries)

    threshold = _percentile(all_abs, percentile)

    results: List[OutlierEntry] = []
    for r in reports:
        for e in r.entries:
            if abs(e.drift_seconds) > threshold:
                results.append(
                    OutlierEntry(
                        server=r.server,
                        job=r.job,
                        drift_seconds=e.drift_seconds,
                        percentile=percentile,
                        threshold_seconds=threshold,
                    )
                )
    results.sort(key=lambda x: abs(x.drift_seconds), reverse=True)
    return results


def format_outliers(outliers: List[OutlierEntry], percentile: float = 95.0) -> str:
    if not outliers:
        return f"No outliers detected above p{percentile:.0f} threshold."
    lines = [f"Outliers (above p{percentile:.0f}): {len(outliers)} found"]
    for o in outliers:
        lines.append(f"  {o}")
    return "\n".join(lines)
