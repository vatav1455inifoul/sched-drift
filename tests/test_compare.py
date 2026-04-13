"""Tests for sched_drift.compare."""
import pytest
from unittest.mock import MagicMock

from sched_drift.compare import (
    CompareEntry,
    _direction,
    compare_windows,
    format_compare,
)
from sched_drift.reporter import DriftReport


def _report(server: str, job: str, avg_drift: float) -> DriftReport:
    r = MagicMock(spec=DriftReport)
    r.server = server
    r.job = job
    r.avg_drift = avg_drift
    return r


# --- _direction ---

def test_direction_worsened():
    assert _direction(10.0) == "worsened"


def test_direction_improved():
    assert _direction(-10.0) == "improved"


def test_direction_unchanged_within_threshold():
    assert _direction(0.5, threshold=1.0) == "unchanged"


def test_direction_exactly_at_threshold_is_worsened():
    assert _direction(1.0, threshold=1.0) == "worsened"


# --- compare_windows ---

def test_compare_windows_basic():
    before = [_report("web1", "backup", 5.0)]
    after = [_report("web1", "backup", 15.0)]
    results = compare_windows(before, after)
    assert len(results) == 1
    entry = results[0]
    assert entry.server == "web1"
    assert entry.job == "backup"
    assert entry.avg_drift_before == pytest.approx(5.0)
    assert entry.avg_drift_after == pytest.approx(15.0)
    assert entry.delta == pytest.approx(10.0)
    assert entry.direction == "worsened"


def test_compare_windows_improved():
    before = [_report("db1", "cleanup", 20.0)]
    after = [_report("db1", "cleanup", 2.0)]
    results = compare_windows(before, after)
    assert results[0].direction == "improved"


def test_compare_windows_new_job_in_after():
    before: list = []
    after = [_report("web1", "sync", 8.0)]
    results = compare_windows(before, after)
    assert len(results) == 1
    assert results[0].avg_drift_before == pytest.approx(0.0)


def test_compare_windows_job_missing_in_after():
    before = [_report("web1", "sync", 8.0)]
    after: list = []
    results = compare_windows(before, after)
    assert results[0].avg_drift_after == pytest.approx(0.0)


def test_compare_windows_sorted_by_server_job():
    before = [
        _report("web2", "alpha", 1.0),
        _report("web1", "beta", 2.0),
    ]
    after = [
        _report("web2", "alpha", 1.0),
        _report("web1", "beta", 2.0),
    ]
    results = compare_windows(before, after)
    keys = [(e.server, e.job) for e in results]
    assert keys == sorted(keys)


# --- format_compare ---

def test_format_compare_empty():
    assert format_compare([]) == "No comparison data."


def test_format_compare_contains_server_and_job():
    entry = CompareEntry(
        server="web1", job="backup",
        avg_drift_before=5.0, avg_drift_after=15.0,
        delta=10.0, direction="worsened",
    )
    out = format_compare([entry])
    assert "web1" in out
    assert "backup" in out
    assert "worsened" in out


def test_format_compare_improved_arrow():
    entry = CompareEntry(
        server="db1", job="clean",
        avg_drift_before=20.0, avg_drift_after=2.0,
        delta=-18.0, direction="improved",
    )
    out = format_compare([entry])
    assert "↓" in out
