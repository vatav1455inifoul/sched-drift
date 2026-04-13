"""Tests for the log entry parser."""

import pytest
from datetime import datetime
from sched_drift.parser import parse_line, parse_log_file, LogEntry


VALID_LINE = "2024-01-15T14:30:05Z [server-01] job=backup_db scheduled=2024-01-15T14:30:00Z"
EARLY_LINE = "2024-01-15T14:29:58Z [server-02] job=cleanup scheduled=2024-01-15T14:30:00Z"
ON_TIME_LINE = "2024-01-15T09:00:00Z [server-03] job=report scheduled=2024-01-15T09:00:00Z"


def test_parse_valid_line():
    entry = parse_line(VALID_LINE)
    assert entry is not None
    assert entry.server == "server-01"
    assert entry.job == "backup_db"
    assert entry.scheduled == datetime(2024, 1, 15, 14, 30, 0)
    assert entry.actual == datetime(2024, 1, 15, 14, 30, 5)


def test_drift_positive_when_late():
    entry = parse_line(VALID_LINE)
    assert entry.drift_seconds == 5.0


def test_drift_negative_when_early():
    entry = parse_line(EARLY_LINE)
    assert entry is not None
    assert entry.drift_seconds == -2.0


def test_drift_zero_when_on_time():
    entry = parse_line(ON_TIME_LINE)
    assert entry is not None
    assert entry.drift_seconds == 0.0


def test_parse_comment_line_returns_none():
    assert parse_line("# this is a comment") is None


def test_parse_empty_line_returns_none():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_malformed_line_returns_none():
    assert parse_line("not a valid log line at all") is None
    assert parse_line("2024-01-15T14:30:05Z [server-01] job=missing_scheduled") is None


def test_parse_log_file(tmp_path):
    log_file = tmp_path / "cron.log"
    log_file.write_text(
        "# header comment\n"
        f"{VALID_LINE}\n"
        "garbage line\n"
        f"{EARLY_LINE}\n"
    )
    entries = parse_log_file(str(log_file))
    assert len(entries) == 2
    assert entries[0].job == "backup_db"
    assert entries[1].job == "cleanup"
