"""Filter log entries and reports by a time window (start/end datetime)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport


@dataclass
class WindowFilter:
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    def matches(self, entry: LogEntry) -> bool:
        """Return True if the entry's actual time falls within [start, end]."""
        t = entry.actual_time
        if self.start and t < self.start:
            return False
        if self.end and t > self.end:
            return False
        return True


def filter_entries(
    entries: List[LogEntry],
    wf: WindowFilter,
) -> List[LogEntry]:
    """Return only entries whose actual_time is within the window."""
    return [e for e in entries if wf.matches(e)]


def filter_reports(
    reports: List[DriftReport],
    wf: WindowFilter,
) -> List[DriftReport]:
    """Return DriftReport objects rebuilt from entries that pass the window."""
    from sched_drift.reporter import build_report

    kept: List[LogEntry] = []
    for r in reports:
        kept.extend(filter_entries(r.entries, wf))
    if not kept:
        return []
    return build_report(kept)


def format_window_summary(reports: List[DriftReport], wf: WindowFilter) -> str:
    """One-line summary of how many reports survived the window filter."""
    start_str = wf.start.isoformat() if wf.start else "*"
    end_str = wf.end.isoformat() if wf.end else "*"
    total = sum(len(r.entries) for r in reports)
    return (
        f"Window [{start_str} → {end_str}]: "
        f"{len(reports)} job(s), {total} entry(ies)"
    )
