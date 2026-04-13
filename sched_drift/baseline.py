"""Baseline management: save and compare drift reports against a stored baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from sched_drift.reporter import DriftReport


@dataclass
class BaselineDiff:
    server: str
    job: str
    baseline_avg: float
    current_avg: float
    delta: float  # current - baseline

    @property
    def direction(self) -> str:
        if self.delta > 0:
            return "worse"
        if self.delta < 0:
            return "better"
        return "unchanged"


def save_baseline(reports: List[DriftReport], path: Path) -> None:
    """Persist average drift values from *reports* to a JSON file."""
    data: Dict[str, Dict[str, float]] = {}
    for r in reports:
        data.setdefault(r.server, {})[r.job] = r.avg_drift
    path.write_text(json.dumps(data, indent=2))


def load_baseline(path: Path) -> Dict[str, Dict[str, float]]:
    """Load a previously saved baseline from *path*.

    Returns an empty dict if the file does not exist.
    """
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def compare_baseline(
    reports: List[DriftReport],
    baseline: Dict[str, Dict[str, float]],
    min_delta: float = 0.0,
) -> List[BaselineDiff]:
    """Return diffs for jobs whose avg drift changed by more than *min_delta* seconds."""
    diffs: List[BaselineDiff] = []
    for r in reports:
        baseline_avg: Optional[float] = baseline.get(r.server, {}).get(r.job)
        if baseline_avg is None:
            continue
        delta = r.avg_drift - baseline_avg
        if abs(delta) > min_delta:
            diffs.append(
                BaselineDiff(
                    server=r.server,
                    job=r.job,
                    baseline_avg=baseline_avg,
                    current_avg=r.avg_drift,
                    delta=delta,
                )
            )
    return diffs


def format_baseline_diff(diffs: List[BaselineDiff]) -> str:
    """Human-readable summary of baseline comparison results."""
    if not diffs:
        return "No significant drift changes detected vs baseline."
    lines = [f"Baseline comparison ({len(diffs)} change(s)):"]
    for d in diffs:
        sign = "+" if d.delta >= 0 else ""
        lines.append(
            f"  [{d.direction.upper()}] {d.server} / {d.job}: "
            f"baseline={d.baseline_avg:.1f}s  current={d.current_avg:.1f}s  "
            f"delta={sign}{d.delta:.1f}s"
        )
    return "\n".join(lines)
