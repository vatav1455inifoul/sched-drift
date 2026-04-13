"""Tests for sched_drift.digest module."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport
from sched_drift.digest import DigestLine, build_digest, format_digest, _status


def _entry(drift: float) -> LogEntry:
    return LogEntry(
        server="srv1",
        job="backup",
        scheduled=datetime(2024, 1, 1, 2, 0, 0),
        actual=datetime(2024, 1, 1, 2, 0, 0),
        drift=drift,
    )


def _report(server: str, job: str, drifts: List[float]) -> DriftReport:
    entries = [_entry(d) for d in drifts]
    for e in entries:
        e.server = server
        e.job = job
    avg = sum(drifts) / len(drifts) if drifts else 0.0
    return DriftReport(
        server=server,
        job=job,
        entries=entries,
        avg_drift=avg,
        late_count=sum(1 for d in drifts if d > 0),
        early_count=sum(1 for d in drifts if d < 0),
    )


def test_status_ok():
    assert _status(30.0) == "ok"


def test_status_warn():
    assert _status(90.0) == "warn"


def test_status_critical():
    assert _status(400.0) == "critical"


def test_status_negative_uses_abs():
    assert _status(-350.0) == "critical"


def test_build_digest_returns_digest_lines():
    reports = [_report("web1", "cleanup", [10.0, 20.0, 30.0])]
    result = build_digest(reports)
    assert len(result) == 1
    assert isinstance(result[0], DigestLine)


def test_build_digest_avg_drift():
    reports = [_report("web1", "cleanup", [10.0, 20.0, 30.0])]
    result = build_digest(reports)
    assert result[0].avg_drift == pytest.approx(20.0, abs=0.01)


def test_build_digest_max_drift():
    reports = [_report("web1", "cleanup", [10.0, -50.0, 30.0])]
    result = build_digest(reports)
    assert result[0].max_drift == pytest.approx(50.0, abs=0.01)


def test_build_digest_sorted_by_abs_avg_desc():
    reports = [
        _report("srv1", "jobA", [10.0]),
        _report("srv1", "jobB", [400.0]),
        _report("srv1", "jobC", [80.0]),
    ]
    result = build_digest(reports)
    assert result[0].job == "jobB"
    assert result[1].job == "jobC"
    assert result[2].job == "jobA"


def test_build_digest_occurrences():
    reports = [_report("web1", "sync", [1.0, 2.0, 3.0, 4.0])]
    result = build_digest(reports)
    assert result[0].occurrences == 4


def test_format_digest_empty():
    assert format_digest([]) == "No drift data available."


def test_format_digest_contains_server_and_job():
    lines = [DigestLine("myserver", "myjob", 45.0, 90.0, 3, "warn")]
    output = format_digest(lines)
    assert "myserver" in output
    assert "myjob" in output


def test_format_digest_shows_status_tag():
    lines = [DigestLine("s", "j", 400.0, 400.0, 1, "critical")]
    output = format_digest(lines)
    assert "[CRIT]" in output


def test_format_digest_summary_line():
    lines = [
        DigestLine("s1", "j1", 10.0, 10.0, 2, "ok"),
        DigestLine("s2", "j2", 400.0, 400.0, 1, "critical"),
    ]
    output = format_digest(lines)
    assert "2 job(s)" in output
    assert "1 ok" in output
    assert "1 critical" in output
