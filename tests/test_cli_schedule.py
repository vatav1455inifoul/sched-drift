"""Tests for sched_drift.cli_schedule."""

import argparse
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from sched_drift.cli_schedule import add_schedule_subparser, run_schedule
from sched_drift.parser import LogEntry


def _make_entry(server="web-01", job="backup", actual=None, scheduled=None):
    actual = actual or datetime(2024, 1, 15, 12, 0, 30)
    scheduled = scheduled or datetime(2024, 1, 15, 12, 0, 0)
    return LogEntry(server=server, job_name=job, actual_time=actual, scheduled_time=scheduled)


def _args(**kwargs):
    defaults = dict(logfile="fake.log", cron="0 12 * * *", window=3600, threshold=None)
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    ns.func = run_schedule
    return ns


# ---------------------------------------------------------------------------
# subparser registration
# ---------------------------------------------------------------------------

def test_add_schedule_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_schedule_subparser(sub)
    args = parser.parse_args(["schedule", "my.log", "* * * * *"])
    assert args.logfile == "my.log"
    assert args.cron == "* * * * *"


def test_add_schedule_subparser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_schedule_subparser(sub)
    args = parser.parse_args(["schedule", "my.log", "* * * * *"])
    assert args.window == 3600
    assert args.threshold is None


# ---------------------------------------------------------------------------
# run_schedule
# ---------------------------------------------------------------------------

def test_run_schedule_no_entries_returns_1(capsys):
    with patch("sched_drift.cli_schedule.parse_log_file", return_value=[]):
        rc = run_schedule(_args())
    assert rc == 1
    captured = capsys.readouterr()
    assert "No valid" in captured.err


def test_run_schedule_no_matches_prints_message(capsys):
    entry = _make_entry()
    with patch("sched_drift.cli_schedule.parse_log_file", return_value=[entry]), \
         patch("sched_drift.cli_schedule.match_schedule", return_value=None):
        rc = run_schedule(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "could not be matched" in captured.out or "No entries" in captured.out


def test_run_schedule_prints_drift_table(capsys):
    pytest.importorskip("croniter")
    entry = _make_entry(actual=datetime(2024, 1, 15, 12, 0, 45))
    with patch("sched_drift.cli_schedule return_value=[entry]):
        rc = run_schedule(_args(cron="0 12 * * *"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "web-01" in out
    

def test_run_schedule_threshold_filters_small_drift(capsys):
    pytest.importorskip("croniter")
    # 5-second drift, threshold=60 — should be filtered out
    entry = _make_entry(actual=datetime(2024, 1, 15, 12, 0, 5))
    with patch("sched_drift.cli_schedule.parse_log_file", return_value=[entry]):
        rc = run_schedule(_args(cron="0 12 * * *", threshold=60.0))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No entries exceeded" in out
