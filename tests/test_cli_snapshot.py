"""Tests for sched_drift.cli_snapshot."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sched_drift.cli_snapshot import add_snapshot_subparser, run_snapshot
from sched_drift.snapshot import SnapshotEntry, save_snapshot
from sched_drift.parser import LogEntry
from datetime import datetime, timezone


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"snapshot_cmd": "capture", "logs": ["a.log"], "out": "snap.json"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_entry(server="web1", job="backup") -> LogEntry:
    return LogEntry(
        server=server,
        job=job,
        scheduled=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        actual=datetime(2024, 1, 1, 0, 0, 10, tzinfo=timezone.utc),
    )


def test_add_snapshot_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    add_snapshot_subparser(subs)
    args = parser.parse_args(["snapshot", "capture", "a.log"])
    assert args.snapshot_cmd == "capture"


def test_add_snapshot_subparser_diff_defaults():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    add_snapshot_subparser(subs)
    args = parser.parse_args(["snapshot", "diff", "before.json", "after.json"])
    assert args.before == "before.json"
    assert args.after == "after.json"


def test_run_snapshot_capture_no_entries_returns_1(tmp_path):
    from sched_drift.multi_log import MultiLogResult
    mock_result = MagicMock(spec=MultiLogResult)
    mock_result.entries = []
    with patch("sched_drift.cli_snapshot.load_logs", return_value=mock_result):
        args = _args(snapshot_cmd="capture", logs=["a.log"], out=str(tmp_path / "s.json"))
        assert run_snapshot(args) == 1


def test_run_snapshot_capture_writes_file(tmp_path):
    from sched_drift.multi_log import MultiLogResult
    entry = _make_entry()
    mock_result = MagicMock(spec=MultiLogResult)
    mock_result.entries = [entry]
    out = str(tmp_path / "snap.json")
    with patch("sched_drift.cli_snapshot.load_logs", return_value=mock_result):
        args = _args(snapshot_cmd="capture", logs=["a.log"], out=out)
        rc = run_snapshot(args)
    assert rc == 0
    assert Path(out).exists()


def test_run_snapshot_diff_missing_before_returns_1(tmp_path):
    after_path = str(tmp_path / "after.json")
    save_snapshot([SnapshotEntry("s1", "j1", 1.0, 2.0, 1)], after_path)
    args = _args(
        snapshot_cmd="diff",
        before=str(tmp_path / "missing.json"),
        after=after_path,
    )
    assert run_snapshot(args) == 1


def test_run_snapshot_diff_outputs_result(tmp_path, capsys):
    before_path = str(tmp_path / "before.json")
    after_path = str(tmp_path / "after.json")
    save_snapshot([SnapshotEntry("s1", "j1", 5.0, 10.0, 3)], before_path)
    save_snapshot([SnapshotEntry("s1", "j1", 20.0, 30.0, 3)], after_path)
    args = _args(snapshot_cmd="diff", before=before_path, after=after_path)
    rc = run_snapshot(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert "j1" in captured.out
