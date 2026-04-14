"""Normalize drift values across entries for cross-server comparison."""

from dataclasses import dataclass
from typing import List, Optional
from sched_drift.parser import LogEntry


@dataclass
class NormalizedEntry:
    entry: LogEntry
    raw_drift: float
    normalized: float  # 0.0 to 1.0 relative to observed range
    z_score: Optional[float]

    @property
    def server(self) -> str:
        return self.entry.server

    @property
    def job(self) -> str:
        return self.entry.job


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def normalize_entries(entries: List[LogEntry]) -> List[NormalizedEntry]:
    """Normalize drift values relative to the full range of observed drift."""
    if not entries:
        return []

    drifts = [float(e.drift) for e in entries]
    min_d = min(drifts)
    max_d = max(drifts)
    span = max_d - min_d

    mean = _mean(drifts)
    std = _stddev(drifts, mean)

    results = []
    for entry, drift in zip(entries, drifts):
        normalized = (drift - min_d) / span if span != 0 else 0.5
        z = (drift - mean) / std if std > 0 else None
        results.append(NormalizedEntry(
            entry=entry,
            raw_drift=drift,
            normalized=round(normalized, 4),
            z_score=round(z, 4) if z is not None else None,
        ))
    return results


def format_normalized(entries: List[NormalizedEntry]) -> str:
    """Render a table of normalized drift entries."""
    if not entries:
        return "No entries to normalize."

    lines = [f"{'SERVER':<20} {'JOB':<20} {'DRIFT(s)':>10} {'NORM':>8} {'Z-SCORE':>9}"]
    lines.append("-" * 70)
    for e in entries:
        z = f"{e.z_score:>9.3f}" if e.z_score is not None else "       N/A"
        lines.append(
            f"{e.server:<20} {e.job:<20} {e.raw_drift:>10.1f} "
            f"{e.normalized:>8.4f}{z}"
        )
    return "\n".join(lines)
