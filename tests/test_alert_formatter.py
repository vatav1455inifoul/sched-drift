"""Tests for alert formatting utilities."""

import pytest
from sched_drift.alerts import Alert
from sched_drift.alert_formatter import (
    format_alerts,
    alerts_by_severity,
    has_critical,
)


def _make_alert(severity="warning", rule="test_rule", server="srv1", job="myjob"):
    return Alert(
        rule_name=rule,
        server=server,
        job=job,
        message="something exceeded threshold",
        severity=severity,
    )


def test_format_alerts_empty():
    result = format_alerts([])
    assert result == "No alerts triggered."


def test_format_alerts_shows_count():
    alerts = [_make_alert(), _make_alert(severity="critical")]
    result = format_alerts(alerts)
    assert "2 triggered" in result


def test_format_alerts_includes_server_and_job():
    alerts = [_make_alert(server="db-02", job="vacuum")]
    result = format_alerts(alerts)
    assert "db-02" in result
    assert "vacuum" in result


def test_format_alerts_warning_prefix():
    alerts = [_make_alert(severity="warning")]
    result = format_alerts(alerts)
    assert "[WARN]" in result


def test_format_alerts_critical_prefix():
    alerts = [_make_alert(severity="critical")]
    result = format_alerts(alerts)
    assert "[CRIT]" in result


def test_format_alerts_color_mode_adds_escape_codes():
    alerts = [_make_alert(severity="critical")]
    result = format_alerts(alerts, use_color=True)
    assert "\033[" in result


def test_alerts_by_severity_groups_correctly():
    alerts = [
        _make_alert(severity="warning"),
        _make_alert(severity="critical"),
        _make_alert(severity="warning"),
    ]
    grouped = alerts_by_severity(alerts)
    assert len(grouped["warning"]) == 2
    assert len(grouped["critical"]) == 1


def test_has_critical_true():
    alerts = [_make_alert(severity="warning"), _make_alert(severity="critical")]
    assert has_critical(alerts) is True


def test_has_critical_false():
    alerts = [_make_alert(severity="warning")]
    assert has_critical(alerts) is False


def test_has_critical_empty():
    assert has_critical([]) is False
