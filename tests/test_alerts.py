"""Tests for alert evaluation logic."""

import pytest
from sched_drift.alerts import AlertRule, Alert, evaluate_alerts, DEFAULT_RULES
from sched_drift.reporter import DriftReport, summary as make_summary
from sched_drift.parser import LogEntry
from datetime import datetime


def _make_entry(server, job, scheduled_str, actual_str):
    fmt = "%Y-%m-%d %H:%M:%S"
    return LogEntry(
        server=server,
        job=job,
        scheduled=datetime.strptime(scheduled_str, fmt),
        actual=datetime.strptime(actual_str, fmt),
    )


def _report_from_entries(entries):
    from sched_drift.reporter import build_report
    return build_report(entries)


def test_no_alerts_when_within_thresholds():
    entries = [
        _make_entry("srv1", "backup", "2024-01-01 02:00:00", "2024-01-01 02:00:10"),
        _make_entry("srv1", "backup", "2024-01-02 02:00:00", "2024-01-02 02:00:05"),
    ]
    report = _report_from_entries(entries)
    alerts = evaluate_alerts(report)
    assert alerts == []


def test_high_avg_drift_triggers_warning():
    entries = [
        _make_entry("srv1", "cleanup", "2024-01-01 03:00:00", "2024-01-01 03:01:30"),
        _make_entry("srv1", "cleanup", "2024-01-02 03:00:00", "2024-01-02 03:01:20"),
    ]
    report = _report_from_entries(entries)
    rule = AlertRule(name="high_avg_drift", max_avg_drift_seconds=60.0)
    alerts = evaluate_alerts(report, rules=[rule])
    assert any(a.rule_name == "high_avg_drift" and a.severity == "warning" for a in alerts)


def test_critical_single_drift_triggers_critical():
    entries = [
        _make_entry("srv2", "sync", "2024-01-01 04:00:00", "2024-01-01 04:06:00"),
    ]
    report = _report_from_entries(entries)
    rule = AlertRule(name="critical_single_drift", max_single_drift_seconds=300.0)
    alerts = evaluate_alerts(report, rules=[rule])
    assert any(a.severity == "critical" for a in alerts)


def test_frequent_late_count_triggers_warning():
    entries = [
        _make_entry("srv3", "report", f"2024-01-0{i} 05:00:00", f"2024-01-0{i} 05:00:30")
        for i in range(1, 7)
    ]
    report = _report_from_entries(entries)
    rule = AlertRule(name="frequent_late_runs", min_late_count=5)
    alerts = evaluate_alerts(report, rules=[rule])
    assert any(a.rule_name == "frequent_late_runs" for a in alerts)


def test_evaluate_alerts_uses_default_rules_when_none_given():
    entries = [
        _make_entry("srv1", "job", "2024-01-01 00:00:00", "2024-01-01 00:00:01"),
    ]
    report = _report_from_entries(entries)
    # Should not raise, and returns a list
    result = evaluate_alerts(report)
    assert isinstance(result, list)


def test_alert_contains_server_and_job():
    entries = [
        _make_entry("web-01", "deploy", "2024-01-01 10:00:00", "2024-01-01 10:06:00"),
    ]
    report = _report_from_entries(entries)
    rule = AlertRule(name="critical_single_drift", max_single_drift_seconds=300.0)
    alerts = evaluate_alerts(report, rules=[rule])
    assert alerts[0].server == "web-01"
    assert alerts[0].job == "deploy"
