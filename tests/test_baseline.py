"""Tests for sched_drift.baseline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sched_drift.baseline import (
    BaselineDiff,
    compare_baseline,
    format_baseline_diff,
    load_baseline,
    save_baseline,
)
from sched_drift.reporter import DriftReport


def _report(server: str, job: str, avg: float) -> DriftReport:
    return DriftReport(server=server, job=job, avg_drift=avg, max_drift=avg, min_drift=avg, late_count=0, early_count=0, total=1)


# --- save / load ---

def test_save_baseline_creates_file(tmp_path: Path) -> None:
    p = tmp_path / "baseline.json"
    save_baseline([_report("web1", "backup", 30.0)], p)
    assert p.exists()


def test_save_baseline_content(tmp_path: Path) -> None:
    p = tmp_path / "baseline.json"
    save_baseline([_report("web1", "backup", 30.0), _report("web1", "cleanup", -5.0)], p)
    data = json.loads(p.read_text())
    assert data["web1"]["backup"] == pytest.approx(30.0)
    assert data["web1"]["cleanup"] == pytest.approx(-5.0)


def test_load_baseline_missing_file_returns_empty(tmp_path: Path) -> None:
    result = load_baseline(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_baseline_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "baseline.json"
    reports = [_report("srv", "job", 12.5)]
    save_baseline(reports, p)
    loaded = load_baseline(p)
    assert loaded["srv"]["job"] == pytest.approx(12.5)


# --- compare ---

def test_compare_no_change_returns_empty() -> None:
    baseline = {"web1": {"backup": 30.0}}
    diffs = compare_baseline([_report("web1", "backup", 30.0)], baseline)
    assert diffs == []


def test_compare_detects_worse() -> None:
    baseline = {"web1": {"backup": 10.0}}
    diffs = compare_baseline([_report("web1", "backup", 40.0)], baseline)
    assert len(diffs) == 1
    assert diffs[0].direction == "worse"
    assert diffs[0].delta == pytest.approx(30.0)


def test_compare_detects_better() -> None:
    baseline = {"web1": {"backup": 50.0}}
    diffs = compare_baseline([_report("web1", "backup", 20.0)], baseline)
    assert diffs[0].direction == "better"


def test_compare_min_delta_filters_small_changes() -> None:
    baseline = {"web1": {"backup": 10.0}}
    diffs = compare_baseline([_report("web1", "backup", 11.0)], baseline, min_delta=5.0)
    assert diffs == []


def test_compare_unknown_job_skipped() -> None:
    baseline = {"web1": {"other": 10.0}}
    diffs = compare_baseline([_report("web1", "backup", 50.0)], baseline)
    assert diffs == []


# --- format ---

def test_format_empty() -> None:
    assert "No significant" in format_baseline_diff([])


def test_format_shows_server_and_job() -> None:
    diff = BaselineDiff(server="web1", job="backup", baseline_avg=10.0, current_avg=40.0, delta=30.0)
    output = format_baseline_diff([diff])
    assert "web1" in output
    assert "backup" in output
    assert "WORSE" in output
