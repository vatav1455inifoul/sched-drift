"""Group and aggregate drift entries by time window (hour, day, weekday)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Literal

from sched_drift.parser import LogEntry

Window = Literal["hour", "day", "weekday"]

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass
class GroupBucket:
    label: str
    count: int
    avg_drift: float
    max_drift: float
    min_drift: float
    entries: List[LogEntry] = field(default_factory=list, repr=False)


def _bucket_key(entry: LogEntry, window: Window) -> str:
    t = entry.actual_time
    if window == "hour":
        return f"{t.hour:02d}:00"
    if window == "day":
        return t.strftime("%Y-%m-%d")
    if window == "weekday":
        return WEEKDAY_NAMES[t.weekday()]
    raise ValueError(f"Unknown window: {window}")


def group_by_window(
    entries: List[LogEntry],
    window: Window = "hour",
) -> List[GroupBucket]:
    """Return buckets of entries grouped by the given time window."""
    buckets: Dict[str, List[LogEntry]] = defaultdict(list)
    for entry in entries:
        key = _bucket_key(entry, window)
        buckets[key].append(entry)

    result: List[GroupBucket] = []
    for label in sorted(buckets):
        group = buckets[label]
        drifts = [e.drift for e in group]
        result.append(
            GroupBucket(
                label=label,
                count=len(group),
                avg_drift=sum(drifts) / len(drifts),
                max_drift=max(drifts),
                min_drift=min(drifts),
                entries=group,
            )
        )
    return result


def format_groupby(buckets: List[GroupBucket], window: Window) -> str:
    """Format grouped buckets into a human-readable table string."""
    if not buckets:
        return "No data to group."

    lines = [f"Drift grouped by {window}:", ""]
    header = f"  {'Label':<12} {'Count':>6} {'Avg(s)':>9} {'Min(s)':>9} {'Max(s)':>9}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    for b in buckets:
        lines.append(
            f"  {b.label:<12} {b.count:>6} {b.avg_drift:>9.1f}"
            f" {b.min_drift:>9.1f} {b.max_drift:>9.1f}"
        )
    return "\n".join(lines)
