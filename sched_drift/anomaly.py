"""Detect anomalous drift values using simple statistical outlier detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import statistics

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport


@dataclass
class Anomaly:
    server: str
    job: str
    drift: float
    mean: float
    stddev: float
    z_score: float

    @property
    def label(self) -> str:
        direction = "late" if self.drift > 0 else "early"
        return f"{self.server}/{self.job} drift={self.drift:+.1f}s ({direction}, z={self.z_score:.2f})"


def _z_scores(values: List[float]) -> Optional[List[float]]:
    """Return z-scores for a list of values, or None if stddev is zero."""
    if len(values) < 2:
        return None
    mean = statistics.mean(values)
    stddev = statistics.pstdev(values)
    if stddev == 0:
        return None
    return [(v - mean) / stddev for v in values]


def detect_anomalies(
    reports: List[DriftReport],
    entries: List[LogEntry],
    z_threshold: float = 2.0,
) -> List[Anomaly]:
    """Identify log entries whose drift is a statistical outlier per server+job."""
    from collections import defaultdict

    grouped: dict[tuple[str, str], List[LogEntry]] = defaultdict(list)
    for entry in entries:
        grouped[(entry.server, entry.job)].append(entry)

    anomalies: List[Anomaly] = []
    for (server, job), group in grouped.items():
        drifts = [e.drift for e in group]
        zs = _z_scores(drifts)
        if zs is None:
            continue
        mean = statistics.mean(drifts)
        stddev = statistics.pstdev(drifts)
        for entry, z in zip(group, zs):
            if abs(z) >= z_threshold:
                anomalies.append(
                    Anomaly(
                        server=server,
                        job=job,
                        drift=entry.drift,
                        mean=mean,
                        stddev=stddev,
                        z_score=z,
                    )
                )
    return anomalies


def format_anomalies(anomalies: List[Anomaly]) -> str:
    """Return a human-readable summary of detected anomalies."""
    if not anomalies:
        return "No anomalies detected."
    lines = [f"Anomalies detected: {len(anomalies)}"]
    for a in anomalies:
        lines.append(f"  !! {a.label}")
    return "\n".join(lines)
