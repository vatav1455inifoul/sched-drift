"""Deduplication of log entries based on server, job, and scheduled time."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport


@dataclass
class DedupResult:
    entries: List[LogEntry]
    duplicates_removed: int
    duplicate_keys: List[Tuple[str, str, str]]  # (server, job, scheduled_time)


def _entry_key(entry: LogEntry) -> Tuple[str, str, str]:
    """Return a hashable key uniquely identifying a scheduled execution."""
    return (entry.server, entry.job, entry.scheduled_time.isoformat())


def dedup_entries(entries: List[LogEntry]) -> DedupResult:
    """Remove duplicate log entries, keeping the first occurrence."""
    seen: Dict[Tuple[str, str, str], bool] = {}
    unique: List[LogEntry] = []
    dup_keys: List[Tuple[str, str, str]] = []

    for entry in entries:
        key = _entry_key(entry)
        if key in seen:
            dup_keys.append(key)
        else:
            seen[key] = True
            unique.append(entry)

    return DedupResult(
        entries=unique,
        duplicates_removed=len(dup_keys),
        duplicate_keys=dup_keys,
    )


def dedup_reports(reports: List[DriftReport]) -> List[DriftReport]:
    """Deduplicate entries within each DriftReport in-place (returns new list)."""
    deduped = []
    for report in reports:
        result = dedup_entries(report.entries)
        deduped.append(
            DriftReport(
                server=report.server,
                job=report.job,
                entries=result.entries,
            )
        )
    return deduped


def format_dedup(result: DedupResult) -> str:
    """Return a human-readable summary of deduplication results."""
    lines = [f"Deduplication complete: {result.duplicates_removed} duplicate(s) removed."]
    if result.duplicate_keys:
        lines.append("Duplicate entries (server, job, scheduled_time):")
        for server, job, sched in result.duplicate_keys:
            lines.append(f"  [{server}] {job} @ {sched}")
    else:
        lines.append("No duplicates found.")
    return "\n".join(lines)
