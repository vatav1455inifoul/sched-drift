"""Tests for sched_drift.correlation."""

import pytest
from sched_drift.reporter import DriftReport
from sched_drift.correlation import (
    CorrelationResult,
    _same_direction,
    correlate,
    format_correlation,
)


def _report(server: str, job: str, avg_drift: float) -> DriftReport:
    return DriftReport(
        server=server,
        job=job,
        count=10,
        avg_drift=avg_drift,
        max_drift=avg_drift + 5,
        min_drift=avg_drift - 5,
        late_count=3,
        early_count=1,
    )


def test_same_direction_all_positive():
    assert _same_direction([10.0, 20.0, 15.0]) is True


def test_same_direction_all_negative():
    assert _same_direction([-5.0, -10.0, -3.0]) is True


def test_same_direction_mixed():
    assert _same_direction([10.0, -5.0]) is False


def test_same_direction_single_value():
    assert _same_direction([10.0]) is False


def test_correlate_skips_single_server_jobs():
    reports = [_report("web1", "backup", 15.0)]
    results = correlate(reports)
    assert results == []


def test_correlate_groups_by_job():
    reports = [
        _report("web1", "backup", 20.0),
        _report("web2", "backup", 25.0),
        _report("web1", "cleanup", 5.0),
        _report("web2", "cleanup", 8.0),
    ]
    results = correlate(reports)
    jobs = {r.job for r in results}
    assert jobs == {"backup", "cleanup"}


def test_correlate_systemic_when_same_direction_small_spread():
    reports = [
        _report("web1", "backup", 20.0),
        _report("web2", "backup", 25.0),
    ]
    results = correlate(reports, spread_threshold=30.0)
    assert len(results) == 1
    assert results[0].is_systemic is True


def test_correlate_isolated_when_large_spread():
    reports = [
        _report("web1", "backup", 2.0),
        _report("web2", "backup", 90.0),
    ]
    results = correlate(reports, spread_threshold=30.0)
    assert results[0].is_systemic is False


def test_correlate_spread_value():
    reports = [
        _report("web1", "backup", 10.0),
        _report("web2", "backup", 40.0),
    ]
    results = correlate(reports)
    assert results[0].spread == pytest.approx(30.0)


def test_format_correlation_empty():
    out = format_correlation([])
    assert "No cross-server" in out


def test_format_correlation_includes_job_and_servers():
    reports = [
        _report("web1", "backup", 20.0),
        _report("web2", "backup", 22.0),
    ]
    results = correlate(reports)
    out = format_correlation(results)
    assert "backup" in out
    assert "web1" in out
    assert "web2" in out


def test_format_correlation_systemic_tag():
    reports = [
        _report("web1", "sync", 15.0),
        _report("web2", "sync", 18.0),
    ]
    results = correlate(reports)
    out = format_correlation(results)
    assert "SYSTEMIC" in out
