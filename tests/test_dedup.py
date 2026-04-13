"""Tests for sched_drift.dedup."""

from datetime import datetime, timezone

import pytest

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport
from sched_drift.dedup import (
    DedupResult,
    _entry_key,
    dedup_entries,
    dedup_reports,
    format_dedup,
)


def _entry(
    server="srv1",
    job="backup",
    scheduled="2024-01-01T02:00:00",
    actual="2024-01-01T02:00:05",
) -> LogEntry:
    fmt = "%Y-%m-%dT%H:%M:%S"
    return LogEntry(
        server=server,
        job=job,
        scheduled_time=datetime.strptime(scheduled, fmt).replace(tzinfo=timezone.utc),
        actual_time=datetime.strptime(actual, fmt).replace(tzinfo=timezone.utc),
    )


def test_entry_key_uses_server_job_scheduled():
    e = _entry(server="s", job="j", scheduled="2024-01-01T00:00:00")
    key = _entry_key(e)
    assert key == ("s", "j", "2024-01-01T00:00:00+00:00")


def test_dedup_entries_no_duplicates():
    entries = [_entry(scheduled="2024-01-01T02:00:00"), _entry(scheduled="2024-01-01T03:00:00")]
    result = dedup_entries(entries)
    assert result.duplicates_removed == 0
    assert len(result.entries) == 2
    assert result.duplicate_keys == []


def test_dedup_entries_removes_exact_duplicate():
    e1 = _entry()
    e2 = _entry()  # same key
    result = dedup_entries([e1, e2])
    assert result.duplicates_removed == 1
    assert len(result.entries) == 1


def test_dedup_entries_keeps_first_occurrence():
    e1 = _entry(actual="2024-01-01T02:00:05")
    e2 = _entry(actual="2024-01-01T02:00:99")  # same key, different actual
    result = dedup_entries([e1, e2])
    assert result.entries[0].actual_time == e1.actual_time


def test_dedup_entries_multiple_duplicates():
    base = _entry()
    result = dedup_entries([base, base, base])
    assert result.duplicates_removed == 2
    assert len(result.entries) == 1


def test_dedup_entries_different_servers_not_deduped():
    e1 = _entry(server="srv1")
    e2 = _entry(server="srv2")
    result = dedup_entries([e1, e2])
    assert result.duplicates_removed == 0
    assert len(result.entries) == 2


def test_dedup_reports_returns_same_count():
    r1 = DriftReport(server="srv1", job="backup", entries=[_entry(), _entry()])
    reports = dedup_reports([r1])
    assert len(reports) == 1
    assert reports[0].server == "srv1"


def test_dedup_reports_deduplicates_entries():
    r1 = DriftReport(server="srv1", job="backup", entries=[_entry(), _entry()])
    reports = dedup_reports([r1])
    assert len(reports[0].entries) == 1


def test_format_dedup_no_duplicates():
    result = DedupResult(entries=[], duplicates_removed=0, duplicate_keys=[])
    output = format_dedup(result)
    assert "0 duplicate(s)" in output
    assert "No duplicates found" in output


def test_format_dedup_with_duplicates():
    result = DedupResult(
        entries=[],
        duplicates_removed=1,
        duplicate_keys=[("srv1", "backup", "2024-01-01T02:00:00+00:00")],
    )
    output = format_dedup(result)
    assert "1 duplicate(s)" in output
    assert "srv1" in output
    assert "backup" in output
