"""Tests for sched_drift.topn."""

import pytest
from datetime import datetime
from sched_drift.parser import LogEntry
from sched_drift.reporter import build_report
from sched_drift.topn import top_n, format_topn, TopEntry


def _entry(server: str, job: str, drift: float) -> LogEntry:
    return LogEntry(
        server=server,
        job=job,
        scheduled=datetime(2024, 1, 1, 12, 0, 0),
        actual=datetime(2024, 1, 1, 12, 0, 0),
        drift_seconds=drift,
    )


def _reports(entries):
    return build_report(entries)


def _make_entries():
    return [
        _entry("web-01", "backup", 120.0),
        _entry("web-01", "backup", 100.0),
        _entry("web-01", "cleanup", 10.0),
        _entry("db-01", "vacuum", 300.0),
        _entry("db-01", "vacuum", 280.0),
        _entry("db-01", "stats", -50.0),
        _entry("cache-01", "flush", 5.0),
    ]


def test_top_n_returns_correct_count():
    reports = _reports(_make_entries())
    result = top_n(reports, n=2)
    assert len(result) == 2


def test_top_n_sorted_by_avg_drift_descending():
    reports = _reports(_make_entries())
    result = top_n(reports, n=3)
    abs_avgs = [abs(e.avg_drift) for e in result]
    assert abs_avgs == sorted(abs_avgs, reverse=True)


def test_top_n_by_max_drift():
    reports = _reports(_make_entries())
    result = top_n(reports, n=3, by_max=True)
    max_drifts = [abs(e.max_drift) for e in result]
    assert max_drifts == sorted(max_drifts, reverse=True)


def test_top_n_filter_by_server():
    reports = _reports(_make_entries())
    result = top_n(reports, n=10, server="web-01")
    assert all(e.server == "web-01" for e in result)
    assert len(result) == 2


def test_top_n_returns_topentry_fields():
    reports = _reports(_make_entries())
    result = top_n(reports, n=1)
    e = result[0]
    assert isinstance(e, TopEntry)
    assert e.server
    assert e.job
    assert isinstance(e.avg_drift, float)
    assert isinstance(e.max_drift, float)
    assert e.count > 0


def test_top_n_empty_reports():
    result = top_n([], n=5)
    assert result == []


def test_format_topn_empty():
    output = format_topn([])
    assert "No drift data" in output


def test_format_topn_shows_server_and_job():
    reports = _reports(_make_entries())
    result = top_n(reports, n=3)
    output = format_topn(result)
    assert "web-01" in output or "db-01" in output
    assert "vacuum" in output or "backup" in output


def test_format_topn_by_max_label():
    reports = _reports(_make_entries())
    result = top_n(reports, n=2, by_max=True)
    output = format_topn(result, by_max=True)
    assert "max drift" in output


def test_format_topn_default_label():
    reports = _reports(_make_entries())
    result = top_n(reports, n=2)
    output = format_topn(result, by_max=False)
    assert "avg drift" in output
