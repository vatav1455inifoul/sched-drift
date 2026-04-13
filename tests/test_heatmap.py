"""Tests for sched_drift.heatmap."""

from datetime import datetime

import pytest

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport
from sched_drift.heatmap import HeatmapRow, build_heatmap, format_heatmap


def _entry(hour: int, drift: int = 0) -> LogEntry:
    actual = datetime(2024, 1, 15, hour, 0, 0)
    scheduled = datetime(2024, 1, 15, hour, 0, 0)
    return LogEntry(
        server="web-01",
        job="backup",
        scheduled_time=scheduled,
        actual_time=actual,
        drift_seconds=drift,
    )


def _report(server: str, job: str, entries) -> DriftReport:
    return DriftReport(
        server=server,
        job=job,
        entries=entries,
        avg_drift=0.0,
        max_drift=0,
        min_drift=0,
        late_count=0,
        early_count=0,
    )


def test_build_heatmap_empty_returns_empty():
    assert build_heatmap([]) == []


def test_build_heatmap_buckets_by_hour():
    entries = [_entry(2), _entry(2), _entry(14)]
    report = _report("web-01", "backup", entries)
    rows = build_heatmap([report])
    assert len(rows) == 1
    row = rows[0]
    assert row.buckets[2] == 2
    assert row.buckets[14] == 1
    assert row.buckets[0] == 0


def test_build_heatmap_total():
    entries = [_entry(h) for h in [0, 6, 12, 18]]
    report = _report("web-01", "backup", entries)
    rows = build_heatmap([report])
    assert rows[0].total == 4


def test_build_heatmap_peak_hour():
    entries = [_entry(3), _entry(3), _entry(3), _entry(10)]
    report = _report("web-01", "backup", entries)
    rows = build_heatmap([report])
    assert rows[0].peak_hour == 3


def test_build_heatmap_groups_by_server_and_job():
    r1 = _report("web-01", "backup", [_entry(1)])
    r2 = _report("db-01", "vacuum", [_entry(5)])
    rows = build_heatmap([r1, r2])
    labels = [(r.server, r.job) for r in rows]
    assert ("db-01", "vacuum") in labels
    assert ("web-01", "backup") in labels


def test_format_heatmap_empty():
    result = format_heatmap([])
    assert "No heatmap data" in result


def test_format_heatmap_contains_server_and_job():
    entries = [_entry(8)]
    report = _report("web-01", "backup", entries)
    rows = build_heatmap([report])
    output = format_heatmap(rows)
    assert "web-01" in output
    assert "backup" in output


def test_format_heatmap_shows_peak_hour():
    entries = [_entry(22), _entry(22)]
    report = _report("web-01", "backup", entries)
    rows = build_heatmap([report])
    output = format_heatmap(rows)
    assert "22h" in output
