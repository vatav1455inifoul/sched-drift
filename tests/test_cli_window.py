"""Tests for sched_drift.cli_window."""

import argparse
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from sched_drift.cli_window import add_window_subparser, run_window
from sched_drift.parser import LogEntry


def _entry(server: str, job: str, actual: datetime, drift: float = 5.0) -> LogEntry:
    return LogEntry(
        server=server,
        job=job,
        scheduled_time=actual,
        actual_time=actual,
        drift_seconds=drift,
    )


def _args(**kwargs):
    defaults = {
        "logs": ["a.log"],
        "start": None,
        "end": None,
        "server": None,
    }
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    ns.func = run_window
    return ns


def test_add_window_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_window_subparser(sub)
    args = parser.parse_args(["window", "a.log"])
    assert args.func == run_window


def test_add_window_subparser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_window_subparser(sub)
    args = parser.parse_args(["window", "a.log"])
    assert args.start is None
    assert args.end is None
    assert args.server is None


def test_run_window_no_entries_returns_1():
    from sched_drift.multi_log import MultiLogResult

    mock_result = MultiLogResult(all_entries=[], errors={})
    with patch("sched_drift.cli_window.load_logs", return_value=mock_result):
        rc = run_window(_args())
    assert rc == 1


def test_run_window_no_match_returns_1():
    from sched_drift.multi_log import MultiLogResult

    t = datetime(2024, 1, 10, 8, 0, tzinfo=timezone.utc)
    entries = [_entry("s1", "job1", t)]
    mock_result = MultiLogResult(all_entries=entries, errors={})
    with patch("sched_drift.cli_window.load_logs", return_value=mock_result):
        rc = run_window(_args(start="2025-01-01T00:00:00"))
    assert rc == 1


def test_run_window_matching_entries_returns_0(capsys):
    from sched_drift.multi_log import MultiLogResult

    t = datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
    entries = [_entry("s1", "job1", t, 30.0)]
    mock_result = MultiLogResult(all_entries=entries, errors={})
    with patch("sched_drift.cli_window.load_logs", return_value=mock_result):
        rc = run_window(_args(start="2024-01-01T00:00:00", end="2025-01-01T00:00:00"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "job1" in out or "s1" in out


def test_run_window_prints_errors_for_bad_files(capsys):
    from sched_drift.multi_log import MultiLogResult

    t = datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
    entries = [_entry("s1", "job1", t)]
    mock_result = MultiLogResult(
        all_entries=entries, errors={"missing.log": "file not found"}
    )
    with patch("sched_drift.cli_window.load_logs", return_value=mock_result):
        run_window(_args())
    out = capsys.readouterr().out
    assert "missing.log" in out
