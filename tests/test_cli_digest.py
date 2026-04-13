"""Tests for sched_drift.cli_digest module."""
from __future__ import annotations

import argparse
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from sched_drift.parser import LogEntry
from sched_drift.cli_digest import add_digest_subparser, run_digest


def _entry(server: str, job: str, drift: float) -> LogEntry:
    return LogEntry(
        server=server,
        job=job,
        scheduled=datetime(2024, 3, 1, 6, 0, 0),
        actual=datetime(2024, 3, 1, 6, 0, 0),
        drift=drift,
    )


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(logs=["a.log"], server=None, warn=60.0, critical=300.0, func=run_digest)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_digest_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_digest_subparser(subs)
    parsed = parser.parse_args(["digest", "some.log"])
    assert parsed.func is run_digest


def test_add_digest_subparser_defaults():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_digest_subparser(subs)
    parsed = parser.parse_args(["digest", "x.log"])
    assert parsed.warn == 60.0
    assert parsed.critical == 300.0
    assert parsed.server is None


def test_run_digest_no_entries_returns_1(capsys):
    mock_result = MagicMock()
    mock_result.errors = {}
    mock_result.all_entries = []
    mock_result.entries_for_server.return_value = []

    with patch("sched_drift.cli_digest.load_logs", return_value=mock_result):
        code = run_digest(_args())

    assert code == 1
    captured = capsys.readouterr()
    assert "No log entries" in captured.err


def test_run_digest_prints_table(capsys):
    entries = [
        _entry("web1", "backup", 45.0),
        _entry("web1", "backup", 55.0),
    ]
    mock_result = MagicMock()
    mock_result.errors = {}
    mock_result.all_entries = entries

    with patch("sched_drift.cli_digest.load_logs", return_value=mock_result):
        code = run_digest(_args())

    assert code == 0
    captured = capsys.readouterr()
    assert "web1" in captured.out
    assert "backup" in captured.out


def test_run_digest_warns_on_load_errors(capsys):
    mock_result = MagicMock()
    mock_result.errors = {"missing.log": "File not found"}
    mock_result.all_entries = [_entry("s", "j", 10.0)]

    with patch("sched_drift.cli_digest.load_logs", return_value=mock_result):
        run_digest(_args())

    captured = capsys.readouterr()
    assert "missing.log" in captured.err


def test_run_digest_critical_status_shown(capsys):
    entries = [_entry("db1", "vacuum", 400.0)] * 3
    mock_result = MagicMock()
    mock_result.errors = {}
    mock_result.all_entries = entries

    with patch("sched_drift.cli_digest.load_logs", return_value=mock_result):
        code = run_digest(_args())

    assert code == 0
    captured = capsys.readouterr()
    assert "[CRIT]" in captured.out
