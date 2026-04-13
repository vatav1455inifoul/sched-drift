"""Tests for sched_drift.silencer."""

from datetime import datetime, timedelta

import pytest

from sched_drift.alerts import Alert
from sched_drift.silencer import SilenceRule, apply_silences, format_silenced


def _alert(server="web-01", job="backup", severity="warning", message="drift"):
    return Alert(server=server, job=job, severity=severity, message=message)


# --- SilenceRule.matches ---

def test_matches_exact_server_and_job():
    rule = SilenceRule(server="web-01", job="backup")
    assert rule.matches(_alert(server="web-01", job="backup"))


def test_no_match_wrong_server():
    rule = SilenceRule(server="db-01", job="backup")
    assert not rule.matches(_alert(server="web-01", job="backup"))


def test_no_match_wrong_job():
    rule = SilenceRule(server="web-01", job="cleanup")
    assert not rule.matches(_alert(server="web-01", job="backup"))


def test_matches_any_server_when_none():
    rule = SilenceRule(server=None, job="backup")
    assert rule.matches(_alert(server="any-server", job="backup"))


def test_matches_any_job_when_none():
    rule = SilenceRule(server="web-01", job=None)
    assert rule.matches(_alert(server="web-01", job="any-job"))


def test_matches_all_when_both_none():
    rule = SilenceRule()
    assert rule.matches(_alert(server="x", job="y"))


# --- SilenceRule.is_active ---

def test_is_active_no_expiry():
    rule = SilenceRule()
    assert rule.is_active()


def test_is_active_future_expiry():
    rule = SilenceRule(until=datetime.utcnow() + timedelta(hours=1))
    assert rule.is_active()


def test_is_expired():
    rule = SilenceRule(until=datetime.utcnow() - timedelta(seconds=1))
    assert not rule.is_active()


# --- apply_silences ---

def test_apply_silences_splits_correctly():
    alerts = [_alert(server="web-01"), _alert(server="db-01")]
    rules = [SilenceRule(server="web-01")]
    active, silenced = apply_silences(alerts, rules)
    assert len(active) == 1
    assert active[0].server == "db-01"
    assert len(silenced) == 1
    assert silenced[0].server == "web-01"


def test_apply_silences_expired_rule_does_not_suppress():
    alerts = [_alert(server="web-01")]
    rules = [SilenceRule(server="web-01", until=datetime.utcnow() - timedelta(hours=1))]
    active, silenced = apply_silences(alerts, rules)
    assert len(active) == 1
    assert len(silenced) == 0


def test_apply_silences_no_rules_returns_all_active():
    alerts = [_alert(), _alert(server="db-01")]
    active, silenced = apply_silences(alerts, [])
    assert len(active) == 2
    assert silenced == []


# --- format_silenced ---

def test_format_silenced_empty():
    assert format_silenced([]) == "No alerts silenced."


def test_format_silenced_shows_count():
    result = format_silenced([_alert(), _alert()])
    assert "Silenced 2 alert(s)" in result


def test_format_silenced_includes_server_and_job():
    result = format_silenced([_alert(server="web-01", job="backup")])
    assert "web-01" in result
    assert "backup" in result
