"""Tests for sched_drift.cli_throttle."""

import argparse
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from sched_drift.cli_throttle import add_throttle_subparser, run_throttle
from sched_drift.alerts import Alert
from sched_drift.multi_log import MultiLogResult
from sched_drift.parser import LogEntry


def _entry(server="srv", job="backup", drift=10):
    return LogEntry(
        server=server,
        job=job,
        scheduled=datetime(2024, 1, 1, 2, 0, 0),
        actual=datetime(2024, 1, 1, 2, 0, drift),
        drift_seconds=float(drift),
    )


def _args(**kwargs):
    defaults = dict(
        logs=["fake.log"],
        cooldown=60,
        warn_avg=30.0,
        crit_avg=120.0,
        warn_single=60.0,
        crit_single=300.0,
        reset=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# --- subparser registration ---

def test_add_throttle_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_throttle_subparser(sub)
    args = parser.parse_args(["throttle", "file.log"])
    assert args.func is run_throttle


def test_add_throttle_subparser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_throttle_subparser(sub)
    args = parser.parse_args(["throttle", "file.log"])
    assert args.cooldown == 60
    assert args.warn_avg == 30.0
    assert args.reset is False


# --- run_throttle ---

def test_run_throttle_no_entries_returns_1():
    empty_result = MultiLogResult(entries=[], errors=[])
    with patch("sched_drift.cli_throttle.load_logs", return_value=empty_result):
        rc = run_throttle(_args())
    assert rc == 1


def test_run_throttle_no_alerts_returns_0(capsys):
    result = MultiLogResult(entries=[_entry(drift=5)], errors=[])
    with patch("sched_drift.cli_throttle.load_logs", return_value=result):
        rc = run_throttle(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "suppressed" in out


def test_run_throttle_with_alerts_returns_2(capsys):
    # drift=400 > crit_single=300 => critical alert
    result = MultiLogResult(entries=[_entry(drift=400)], errors=[])
    with patch("sched_drift.cli_throttle.load_logs", return_value=result):
        rc = run_throttle(_args())
    assert rc == 2


def test_run_throttle_reset_clears_state(capsys):
    result = MultiLogResult(entries=[_entry(drift=400)], errors=[])
    with patch("sched_drift.cli_throttle.load_logs", return_value=result):
        run_throttle(_args())          # first run — alert passes
        rc1 = run_throttle(_args())    # second run — suppressed (same process state)
        rc2 = run_throttle(_args(reset=True))  # reset — should fire again
    assert rc1 == 0  # suppressed
    assert rc2 == 2  # fired after reset
