"""Snapshot feature: capture and compare drift state at a point in time."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sched_drift.reporter import DriftReport


@dataclass
class SnapshotEntry:
    server: str
    job: str
    avg_drift: float
    max_drift: float
    sample_count: int


@dataclass
class SnapshotDiff:
    server: str
    job: str
    avg_drift_before: float
    avg_drift_after: float
    delta: float
    direction: str  # "improved", "worsened", "unchanged"


def _direction(delta: float, threshold: float = 1.0) -> str:
    if abs(delta) < threshold:
        return "unchanged"
    return "worsened" if delta > 0 else "improved"


def capture_snapshot(reports: List[DriftReport]) -> List[SnapshotEntry]:
    """Convert DriftReport list into snapshot entries."""
    return [
        SnapshotEntry(
            server=r.server,
            job=r.job,
            avg_drift=round(r.avg_drift, 2),
            max_drift=round(r.max_drift, 2),
            sample_count=r.sample_count,
        )
        for r in reports
    ]


def save_snapshot(entries: List[SnapshotEntry], path: str) -> None:
    """Persist snapshot entries to a JSON file."""
    payload = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "entries": [asdict(e) for e in entries],
    }
    Path(path).write_text(json.dumps(payload, indent=2))


def load_snapshot(path: str) -> List[SnapshotEntry]:
    """Load snapshot entries from a JSON file. Returns empty list if missing."""
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [SnapshotEntry(**e) for e in data.get("entries", [])]


def diff_snapshots(
    before: List[SnapshotEntry], after: List[SnapshotEntry]
) -> List[SnapshotDiff]:
    """Compare two snapshots and return per-job diffs."""
    before_map = {(e.server, e.job): e for e in before}
    diffs: List[SnapshotDiff] = []
    for entry in after:
        key = (entry.server, entry.job)
        if key not in before_map:
            continue
        prev = before_map[key]
        delta = entry.avg_drift - prev.avg_drift
        diffs.append(
            SnapshotDiff(
                server=entry.server,
                job=entry.job,
                avg_drift_before=prev.avg_drift,
                avg_drift_after=entry.avg_drift,
                delta=round(delta, 2),
                direction=_direction(delta),
            )
        )
    return diffs


def format_snapshot_diff(diffs: List[SnapshotDiff]) -> str:
    """Return a human-readable diff summary."""
    if not diffs:
        return "No comparable entries found."
    lines = ["Snapshot diff:", ""]
    for d in diffs:
        arrow = {"improved": "↓", "worsened": "↑", "unchanged": "="}[d.direction]
        lines.append(
            f"  [{d.server}] {d.job}: {d.avg_drift_before:+.1f}s → "
            f"{d.avg_drift_after:+.1f}s  ({arrow} {d.delta:+.1f}s, {d.direction})"
        )
    return "\n".join(lines)
