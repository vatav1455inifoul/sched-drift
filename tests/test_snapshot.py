"""Tests for sched_drift.snapshot."""

import json
import pytest
from pathlib import Path

from sched_drift.snapshot import (
    SnapshotEntry,
    SnapshotDiff,
    capture_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
    format_snapshot_diff,
    _direction,
)
from sched_drift.reporter import DriftReport


def _report(server="web1", job="backup", avg=10.0, max_d=20.0, count=5) -> DriftReport:
    return DriftReport(
        server=server,
        job=job,
        avg_drift=avg,
        max_drift=max_d,
        min_drift=0.0,
        late_count=2,
        early_count=1,
        sample_count=count,
    )


def test_direction_worsened():
    assert _direction(5.0) == "worsened"


def test_direction_improved():
    assert _direction(-5.0) == "improved"


def test_direction_unchanged_within_threshold():
    assert _direction(0.5) == "unchanged"


def test_capture_snapshot_returns_entries():
    reports = [_report("s1", "job1", avg=3.5, max_d=7.0, count=4)]
    entries = capture_snapshot(reports)
    assert len(entries) == 1
    e = entries[0]
    assert e.server == "s1"
    assert e.job == "job1"
    assert e.avg_drift == 3.5
    assert e.max_drift == 7.0
    assert e.sample_count == 4


def test_save_and_load_snapshot_roundtrip(tmp_path):
    path = str(tmp_path / "snap.json")
    entries = [SnapshotEntry("web1", "backup", 12.3, 30.0, 6)]
    save_snapshot(entries, path)
    loaded = load_snapshot(path)
    assert len(loaded) == 1
    assert loaded[0].server == "web1"
    assert loaded[0].avg_drift == 12.3


def test_load_snapshot_missing_file_returns_empty(tmp_path):
    result = load_snapshot(str(tmp_path / "nonexistent.json"))
    assert result == []


def test_save_snapshot_has_captured_at(tmp_path):
    path = str(tmp_path / "snap.json")
    save_snapshot([], path)
    data = json.loads(Path(path).read_text())
    assert "captured_at" in data


def test_diff_snapshots_detects_worsened():
    before = [SnapshotEntry("web1", "job", 5.0, 10.0, 3)]
    after = [SnapshotEntry("web1", "job", 15.0, 20.0, 3)]
    diffs = diff_snapshots(before, after)
    assert len(diffs) == 1
    assert diffs[0].direction == "worsened"
    assert diffs[0].delta == 10.0


def test_diff_snapshots_detects_improved():
    before = [SnapshotEntry("web1", "job", 20.0, 30.0, 3)]
    after = [SnapshotEntry("web1", "job", 5.0, 10.0, 3)]
    diffs = diff_snapshots(before, after)
    assert diffs[0].direction == "improved"


def test_diff_snapshots_skips_new_jobs():
    before: list = []
    after = [SnapshotEntry("web1", "new_job", 5.0, 10.0, 2)]
    diffs = diff_snapshots(before, after)
    assert diffs == []


def test_format_snapshot_diff_empty():
    assert "No comparable" in format_snapshot_diff([])


def test_format_snapshot_diff_contains_server_and_job():
    diffs = [SnapshotDiff("web1", "backup", 5.0, 15.0, 10.0, "worsened")]
    out = format_snapshot_diff(diffs)
    assert "web1" in out
    assert "backup" in out
    assert "worsened" in out
