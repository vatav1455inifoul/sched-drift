"""Tests for sched_drift.outlier."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport
from sched_drift.outlier import (
    OutlierEntry,
    _percentile,
    detect_outliers,
    format_outliers,
)


def _entry(drift: float) -> LogEntry:
    now = datetime(2024, 1, 1, 12, 0, 0)
    return LogEntry(
        server="srv1",
        job="backup",
        scheduled=now,
        actual=now,
        drift_seconds=drift,
    )


def _report(server: str, job: str, drifts: List[float]) -> DriftReport:
    entries = [_entry(d) for d in drifts]
    for e in entries:
        e.server = server
        e.job = job
    avg = sum(drifts) / len(drifts) if drifts else 0.0
    late = sum(1 for d in drifts if d > 0)
    early = sum(1 for d in drifts if d < 0)
    return DriftReport(
        server=server,
        job=job,
        entries=entries,
        avg_drift=avg,
        late_count=late,
        early_count=early,
    )


# --- _percentile ---

def test_percentile_empty_returns_zero():
    assert _percentile([], 95) == 0.0


def test_percentile_single_value():
    assert _percentile([42.0], 95) == 42.0


def test_percentile_p100_returns_max():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert _percentile(values, 100) == 5.0


def test_percentile_p50_returns_median_ish():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    result = _percentile(values, 50)
    assert result in values


# --- detect_outliers ---

def test_detect_outliers_empty_returns_empty():
    assert detect_outliers([]) == []


def test_detect_outliers_flags_large_drift():
    reports = [
        _report("srv1", "job_a", [5, 6, 7, 8, 9, 10, 11, 12, 13, 200]),
    ]
    outliers = detect_outliers(reports, percentile=90)
    assert len(outliers) >= 1
    assert any(abs(o.drift_seconds) == 200 for o in outliers)


def test_detect_outliers_sorted_by_abs_drift_descending():
    reports = [
        _report("srv1", "job_a", [1, 2, 3, 4, 5, 6, 7, 8, 9, 300, 250]),
    ]
    outliers = detect_outliers(reports, percentile=80)
    drifts = [abs(o.drift_seconds) for o in outliers]
    assert drifts == sorted(drifts, reverse=True)


def test_detect_outliers_threshold_stored_on_entry():
    reports = [
        _report("srv1", "job_a", [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]),
    ]
    outliers = detect_outliers(reports, percentile=90)
    for o in outliers:
        assert o.threshold_seconds > 0
        assert o.percentile == 90.0


def test_detect_outliers_no_outliers_when_all_similar():
    reports = [
        _report("srv1", "job_a", [10, 10, 10, 10, 10]),
    ]
    outliers = detect_outliers(reports, percentile=95)
    assert outliers == []


# --- format_outliers ---

def test_format_outliers_empty_message():
    result = format_outliers([], percentile=95)
    assert "No outliers" in result
    assert "p95" in result


def test_format_outliers_shows_count():
    o = OutlierEntry(server="s", job="j", drift_seconds=500.0, percentile=95.0, threshold_seconds=100.0)
    result = format_outliers([o], percentile=95)
    assert "1 found" in result


def test_format_outliers_includes_server_and_job():
    o = OutlierEntry(server="web01", job="cleanup", drift_seconds=-80.0, percentile=95.0, threshold_seconds=50.0)
    result = format_outliers([o])
    assert "web01" in result
    assert "cleanup" in result
