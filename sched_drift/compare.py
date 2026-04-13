"""Compare drift reports across two time windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sched_drift.reporter import DriftReport


@dataclass
class CompareEntry:
    server: str
    job: str
    avg_drift_before: float
    avg_drift_after: float
    delta: float          # after - before
    direction: str        # "improved", "worsened", "unchanged"


def _direction(delta: float, threshold: float = 1.0) -> str:
    if abs(delta) < threshold:
        return "unchanged"
    return "improved" if delta < 0 else "worsened"


def compare_windows(
    before: List[DriftReport],
    after: List[DriftReport],
    threshold: float = 1.0,
) -> List[CompareEntry]:
    """Return per-(server, job) comparison between two report sets."""
    def _index(reports: List[DriftReport]) -> Dict[Tuple[str, str], float]:
        return {(r.server, r.job): r.avg_drift for r in reports}

    before_idx = _index(before)
    after_idx = _index(after)

    keys = sorted(set(before_idx) | set(after_idx))
    results: List[CompareEntry] = []
    for server, job in keys:
        b = before_idx.get((server, job), 0.0)
        a = after_idx.get((server, job), 0.0)
        delta = a - b
        results.append(
            CompareEntry(
                server=server,
                job=job,
                avg_drift_before=b,
                avg_drift_after=a,
                delta=delta,
                direction=_direction(delta, threshold),
            )
        )
    return results


def format_compare(entries: List[CompareEntry]) -> str:
    if not entries:
        return "No comparison data."

    lines = ["Window Comparison Report", "=" * 40]
    for e in entries:
        arrow = {"improved": "↓", "worsened": "↑", "unchanged": "→"}[e.direction]
        lines.append(
            f"[{e.server}] {e.job}: "
            f"{e.avg_drift_before:+.1f}s → {e.avg_drift_after:+.1f}s "
            f"(Δ{e.delta:+.1f}s) {arrow} {e.direction}"
        )
    return "\n".join(lines)
