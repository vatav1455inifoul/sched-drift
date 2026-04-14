"""Tests for sched_drift.throttle."""

from datetime import datetime, timedelta

import pytest

from sched_drift.alerts import Alert
from sched_drift.throttle import (
    ThrottleState,
    _alert_key,
    throttle_alerts,
    format_throttle_summary,
)


def _alert(server="srv1", job="backup", severity="warning", message="drift high"):
    return Alert(server=server, job=job, severity=severity, message=message)


NOW = datetime(2024, 6, 1, 12, 0, 0)


# --- ThrottleState ---

def test_last_seen_returns_none_initially():
    state = ThrottleState()
    assert state.last_seen(("srv1", "backup", "warning")) is None


def test_record_and_last_seen():
    state = ThrottleState()
    key = ("srv1", "backup", "warning")
    state.record(key, NOW)
    assert state.last_seen(key) == NOW


# --- _alert_key ---

def test_alert_key_tuple():
    a = _alert(server="s", job="j", severity="critical")
    assert _alert_key(a) == ("s", "j", "critical")


# --- throttle_alerts ---

def test_new_alert_passes_through():
    state = ThrottleState()
    alerts = [_alert()]
    result = throttle_alerts(alerts, state, cooldown_minutes=60, now=NOW)
    assert len(result) == 1


def test_same_alert_suppressed_within_cooldown():
    state = ThrottleState()
    alert = _alert()
    throttle_alerts([alert], state, cooldown_minutes=60, now=NOW)
    # fire again 30 min later — should be suppressed
    later = NOW + timedelta(minutes=30)
    result = throttle_alerts([alert], state, cooldown_minutes=60, now=later)
    assert result == []


def test_alert_passes_after_cooldown_expires():
    state = ThrottleState()
    alert = _alert()
    throttle_alerts([alert], state, cooldown_minutes=60, now=NOW)
    after_cooldown = NOW + timedelta(minutes=61)
    result = throttle_alerts([alert], state, cooldown_minutes=60, now=after_cooldown)
    assert len(result) == 1


def test_different_severity_treated_separately():
    state = ThrottleState()
    warn = _alert(severity="warning")
    crit = _alert(severity="critical")
    throttle_alerts([warn], state, cooldown_minutes=60, now=NOW)
    # critical is a different key, should pass
    result = throttle_alerts([crit], state, cooldown_minutes=60, now=NOW)
    assert len(result) == 1


def test_multiple_alerts_mixed_suppression():
    state = ThrottleState()
    a1 = _alert(server="s1", job="j1")
    a2 = _alert(server="s2", job="j2")
    throttle_alerts([a1], state, cooldown_minutes=60, now=NOW)
    # a1 suppressed, a2 new
    result = throttle_alerts([a1, a2], state, cooldown_minutes=60, now=NOW)
    assert len(result) == 1
    assert result[0].server == "s2"


def test_state_updated_for_passed_alerts():
    state = ThrottleState()
    alert = _alert()
    throttle_alerts([alert], state, cooldown_minutes=60, now=NOW)
    key = _alert_key(alert)
    assert state.last_seen(key) == NOW


# --- format_throttle_summary ---

def test_format_summary_counts():
    original = [_alert(), _alert(server="s2")]
    passed = [_alert()]
    text = format_throttle_summary(original, passed)
    assert "1 emitted" in text
    assert "1 suppressed" in text


def test_format_summary_lists_passed_alerts():
    alert = _alert(server="srv1", job="backup", severity="warning")
    text = format_throttle_summary([alert], [alert])
    assert "srv1" in text
    assert "backup" in text
    assert "WARNING" in text
