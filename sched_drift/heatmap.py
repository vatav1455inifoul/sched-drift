"""Heatmap module: bucket drift counts by hour-of-day for each server/job pair."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from sched_drift.reporter import DriftReport


@dataclass
class HeatmapRow:
    server: str
    job: str
    # index 0-23 => count of executions in that hour
    buckets: List[int] = field(default_factory=lambda: [0] * 24)

    @property
    def peak_hour(self) -> int:
        """Hour with the most executions."""
        return self.buckets.index(max(self.buckets))

    @property
    def total(self) -> int:
        return sum(self.buckets)


def build_heatmap(reports: List[DriftReport]) -> List[HeatmapRow]:
    """Build one HeatmapRow per (server, job) pair from a list of DriftReports."""
    rows: Dict[Tuple[str, str], HeatmapRow] = {}

    for report in reports:
        key = (report.server, report.job)
        if key not in rows:
            rows[key] = HeatmapRow(server=report.server, job=report.job)
        for entry in report.entries:
            hour = entry.actual_time.hour
            rows[key].buckets[hour] += 1

    return sorted(rows.values(), key=lambda r: (r.server, r.job))


def format_heatmap(rows: List[HeatmapRow]) -> str:
    """Render heatmap rows as a simple text table."""
    if not rows:
        return "No heatmap data available."

    header_hours = "".join(f"{h:>3}" for h in range(24))
    lines = [
        f"{'SERVER/JOB':<30} {header_hours}  PEAK",
        "-" * (30 + 1 + 24 * 3 + 6),
    ]

    for row in rows:
        label = f"{row.server}/{row.job}"
        if len(label) > 30:
            label = label[:27] + "..."
        buckets_str = "".join(f"{b:>3}" for b in row.buckets)
        lines.append(f"{label:<30} {buckets_str}  {row.peak_hour:02d}h")

    return "\n".join(lines)
