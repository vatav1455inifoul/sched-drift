"""Tests for sched_drift.trend module."""

from datetime import datetime, timezone
from sched_drift.parser import LogEntry
from sched_drift.trend import analyze_trends, format_trends, TrendResult, _linear_slope


def _entry(server: str, job: str, drift: float, minute: int = 0) -> LogEntry:
    base = datetime(2024, 1, 1, 12, minute, 0, tzinfo=timezone.utc)
    return LogEntry(
        server=server,
        job=job,
        scheduled_time=base,
        actual_time=base,
        drift=drift,
    )


def test_linear_slope_increasing():
    values = [0.0, 1.0, 2.0, 3.0]
    assert abs(_linear_slope(values) - 1.0) < 1e-6


def test_linear_slope_flat():
    assert _linear_slope([5.0, 5.0, 5.0]) == 0.0


def test_linear_slope_single_value():
    assert _linear_slope([42.0]) == 0.0


def test_analyze_trends_groups_by_server_and_job():
    entries = [
        _entry("web1", "backup", 10, 0),
        _entry("web1", "backup", 20, 1),
        _entry("db1", "cleanup", 5, 0),
    ]
    results = analyze_trends(entries)
    keys = {(r.server, r.job) for r in results}
    assert ("web1", "backup") in keys
    assert ("db1", "cleanup") in keys
    assert len(results) == 2


def test_analyze_trends_worsening():
    entries = [_entry("srv", "job", float(i * 10), i) for i in range(5)]
    results = analyze_trends(entries)
    assert results[0].direction == "worsening"
    assert results[0].slope > 0


def test_analyze_trends_improving():
    entries = [_entry("srv", "job", float(40 - i * 10), i) for i in range(5)]
    results = analyze_trends(entries)
    assert results[0].direction == "improving"
    assert results[0].slope < 0


def test_analyze_trends_stable():
    entries = [_entry("srv", "job", 5.0, i) for i in range(4)]
    results = analyze_trends(entries)
    assert results[0].direction == "stable"
    assert results[0].slope == 0.0


def test_analyze_trends_sample_count():
    entries = [_entry("srv", "job", float(i), i) for i in range(6)]
    results = analyze_trends(entries)
    assert results[0].sample_count == 6


def test_analyze_trends_first_last_drift():
    entries = [_entry("srv", "job", float(i * 5), i) for i in range(3)]
    r = analyze_trends(entries)[0]
    assert r.first_drift == 0.0
    assert r.last_drift == 10.0


def test_format_trends_empty():
    assert format_trends([]) == "No trend data available."


def test_format_trends_contains_server_and_job():
    entries = [_entry("web1", "backup", float(i), i) for i in range(3)]
    output = format_trends(analyze_trends(entries))
    assert "web1" in output
    assert "backup" in output


def test_format_trends_shows_direction_arrow():
    entries = [_entry("s", "j", float(i * 10), i) for i in range(4)]
    output = format_trends(analyze_trends(entries))
    assert "↑" in output or "worsening" in output
