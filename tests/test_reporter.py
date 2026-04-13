"""Tests for sched_drift.reporter module."""

from datetime import datetime
import pytest
from sched_drift.parser import LogEntry
from sched_drift.reporter import build_report, format_report, DriftReport


def make_entry(job="backup", server="web-01", scheduled_offset=0, actual_offset=0):
    base = datetime(2024, 1, 15, 2, 0, 0)
    scheduled = base.replace(second=scheduled_offset)
    actual = base.replace(second=actual_offset)
    return LogEntry(job_name=job, server=server, scheduled_time=scheduled, actual_time=actual)


def test_build_report_groups_by_server_and_job():
    entries = [
        make_entry(job="backup", server="web-01", actual_offset=10),
        make_entry(job="backup", server="web-01", actual_offset=20),
        make_entry(job="cleanup", server="web-01", actual_offset=5),
    ]
    reports = build_report(entries)
    assert len(reports) == 2
    job_names = {r.job_name for r in reports}
    assert "backup" in job_names
    assert "cleanup" in job_names


def test_build_report_avg_drift():
    entries = [
        make_entry(actual_offset=10),
        make_entry(actual_offset=30),
    ]
    reports = build_report(entries)
    assert len(reports) == 1
    assert reports[0].avg_drift_seconds == pytest.approx(20.0)


def test_build_report_late_early_counts():
    entries = [
        make_entry(actual_offset=15),   # late
        make_entry(actual_offset=0),    # on time
        make_entry(scheduled_offset=5, actual_offset=0),  # early
    ]
    reports = build_report(entries)
    assert reports[0].late_runs == 1
    assert reports[0].early_runs == 1
    assert reports[0].on_time_runs == 1


def test_build_report_filter_by_server():
    entries = [
        make_entry(server="web-01", actual_offset=10),
        make_entry(server="web-02", actual_offset=20),
    ]
    reports = build_report(entries, server="web-01")
    assert len(reports) == 1
    assert reports[0].server == "web-01"


def test_build_report_sorted_by_abs_avg_drift():
    entries = [
        make_entry(job="small", actual_offset=2),
        make_entry(job="big", actual_offset=60),
    ]
    reports = build_report(entries)
    assert reports[0].job_name == "big"


def test_format_report_no_data():
    result = format_report([])
    assert result == "No drift data found."


def test_format_report_contains_summary():
    reports = [
        DriftReport(
            job_name="backup", server="web-01",
            total_runs=3, avg_drift_seconds=15.0,
            max_drift_seconds=30.0, min_drift_seconds=5.0,
            late_runs=3, early_runs=0, on_time_runs=0,
        )
    ]
    result = format_report(reports)
    assert "backup" in result
    assert "web-01" in result
    assert "late" in result


def test_format_report_verbose_includes_extra_detail():
    reports = [
        DriftReport(
            job_name="cleanup", server="db-01",
            total_runs=2, avg_drift_seconds=-5.0,
            max_drift_seconds=0.0, min_drift_seconds=-10.0,
            late_runs=0, early_runs=2, on_time_runs=0,
        )
    ]
    result = format_report(reports, verbose=True)
    assert "early=2" in result
    assert "min=" in result
