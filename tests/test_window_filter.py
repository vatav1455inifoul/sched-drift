"""Tests for sched_drift.window_filter."""

from datetime import datetime, timezone

import pytest

from sched_drift.parser import LogEntry
from sched_drift.reporter import build_report
from sched_drift.window_filter import (
    WindowFilter,
    filter_entries,
    filter_reports,
    format_window_summary,
)


def _entry(server: str, job: str, actual: datetime, drift: float = 0.0) -> LogEntry:
    return LogEntry(
        server=server,
        job=job,
        scheduled_time=actual,
        actual_time=actual,
        drift_seconds=drift,
    )


T1 = datetime(2024, 1, 10, 8, 0, tzinfo=timezone.utc)
T2 = datetime(2024, 1, 10, 12, 0, tzinfo=timezone.utc)
T3 = datetime(2024, 1, 10, 16, 0, tzinfo=timezone.utc)


def test_matches_no_bounds_accepts_all():
    wf = WindowFilter()
    e = _entry("s1", "job1", T2)
    assert wf.matches(e) is True


def test_matches_start_boundary_inclusive():
    wf = WindowFilter(start=T2)
    assert wf.matches(_entry("s1", "j", T2)) is True
    assert wf.matches(_entry("s1", "j", T1)) is False


def test_matches_end_boundary_inclusive():
    wf = WindowFilter(end=T2)
    assert wf.matches(_entry("s1", "j", T2)) is True
    assert wf.matches(_entry("s1", "j", T3)) is False


def test_matches_within_range():
    wf = WindowFilter(start=T1, end=T3)
    assert wf.matches(_entry("s1", "j", T2)) is True


def test_matches_outside_range():
    wf = WindowFilter(start=T2, end=T3)
    assert wf.matches(_entry("s1", "j", T1)) is False


def test_filter_entries_returns_subset():
    entries = [
        _entry("s1", "job1", T1),
        _entry("s1", "job1", T2),
        _entry("s1", "job1", T3),
    ]
    wf = WindowFilter(start=T2, end=T3)
    result = filter_entries(entries, wf)
    assert len(result) == 2
    assert all(e.actual_time >= T2 for e in result)


def test_filter_entries_empty_when_none_match():
    entries = [_entry("s1", "job1", T1)]
    wf = WindowFilter(start=T2, end=T3)
    assert filter_entries(entries, wf) == []


def test_filter_reports_returns_filtered_reports():
    entries = [
        _entry("s1", "job1", T1, 10.0),
        _entry("s1", "job1", T2, 20.0),
    ]
    reports = build_report(entries)
    wf = WindowFilter(start=T2)
    result = filter_reports(reports, wf)
    assert len(result) == 1
    assert len(result[0].entries) == 1


def test_filter_reports_empty_when_no_entries_match():
    entries = [_entry("s1", "job1", T1)]
    reports = build_report(entries)
    wf = WindowFilter(start=T3)
    assert filter_reports(reports, wf) == []


def test_format_window_summary_shows_bounds():
    reports = build_report([_entry("s1", "job1", T2)])
    wf = WindowFilter(start=T1, end=T3)
    out = format_window_summary(reports, wf)
    assert "2024-01-10T08:00:00" in out
    assert "2024-01-10T16:00:00" in out


def test_format_window_summary_open_bounds():
    reports = build_report([_entry("s1", "job1", T2)])
    wf = WindowFilter()
    out = format_window_summary(reports, wf)
    assert "*" in out
