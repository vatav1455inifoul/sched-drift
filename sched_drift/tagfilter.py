"""Tag-based filtering for log entries and drift reports."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport


@dataclass
class TagFilter:
    """Filter that matches entries whose job name contains any of the given tags."""

    tags: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    def matches(self, entry: LogEntry) -> bool:
        """Return True when the entry passes the tag filter."""
        job = entry.job_name.lower()

        if self.exclude and any(t.lower() in job for t in self.exclude):
            return False

        if not self.tags:
            return True

        return any(t.lower() in job for t in self.tags)


def filter_entries(
    entries: Iterable[LogEntry],
    tag_filter: TagFilter,
) -> list[LogEntry]:
    """Return only the entries that satisfy *tag_filter*."""
    return [e for e in entries if tag_filter.matches(e)]


def filter_reports(
    reports: Iterable[DriftReport],
    tag_filter: TagFilter,
) -> list[DriftReport]:
    """Return only the reports whose job name satisfies *tag_filter*."""
    return [
        r for r in reports
        if tag_filter.matches(
            # Construct a minimal stand-in entry for matching purposes.
            LogEntry(
                server=r.server,
                job_name=r.job_name,
                scheduled_time=__import__('datetime').datetime.min,
                actual_time=__import__('datetime').datetime.min,
            )
        )
    ]


def format_tag_summary(kept: int, total: int, tag_filter: TagFilter) -> str:
    """Return a human-readable summary of how many entries survived filtering."""
    include_part = ", ".join(tag_filter.tags) if tag_filter.tags else "(all)"
    exclude_part = ", ".join(tag_filter.exclude) if tag_filter.exclude else "(none)"
    return (
        f"Tag filter — include: [{include_part}]  exclude: [{exclude_part}]  "
        f"kept {kept}/{total} entries"
    )
