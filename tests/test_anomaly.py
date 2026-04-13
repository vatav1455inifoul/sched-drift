"""Tests for sched_drift.anomaly module."""

from datetime import datetime
from typing import List

import pytest

from sched_drift.parser import LogEntry
from sched_drift.anomaly import Anomaly, _z_scores, detect_anomalies, format_anomalies


def _entry(server: str, job: str, drift: float) -> LogEntry:
    return LogEntry(
        server=server,
        job=job,
        scheduled=datetime(2024, 1, 1, 12, 0, 0),
        actual=datetime(2024, 1, 1, 12, 0, 0),
        drift=drift,
    )


# --- _z_scores ---

def test_z_scores_returns_none_for_single_value():
    assert _z_scores([42.0]) is None


def test_z_scores_returns_none_for_zero_stddev():
    assert _z_scores([5.0, 5.0, 5.0]) is None


def test_z_scores_length_matches_input():
    result = _z_scores([1.0, 2.0, 3.0, 4.0, 5.0])
    assert result is not None
    assert len(result) == 5


def test_z_scores_outlier_has_high_absolute_z():
    values = [0.0, 0.0, 0.0, 0.0, 100.0]
    zs = _z_scores(values)
    assert zs is not None
    assert abs(zs[-1]) > 2.0


# --- detect_anomalies ---

def test_detect_anomalies_empty_entries():
    result = detect_anomalies([], [])
    assert result == []


def test_detect_anomalies_no_outliers_when_uniform():
    entries = [_entry("web1", "backup", 5.0) for _ in range(5)]
    result = detect_anomalies([], entries)
    assert result == []


def test_detect_anomalies_single_entry_per_group_skipped():
    entries = [_entry("web1", "backup", 999.0)]
    result = detect_anomalies([], entries)
    assert result == []


def test_detect_anomalies_finds_outlier():
    normal = [_entry("web1", "sync", float(i)) for i in range(10)]
    outlier = _entry("web1", "sync", 1000.0)
    entries = normal + [outlier]
    result = detect_anomalies([], entries, z_threshold=2.0)
    assert any(a.drift == 1000.0 for a in result)


def test_detect_anomalies_groups_by_server_and_job():
    # Two jobs — outlier only in job_a
    job_a = [_entry("s1", "job_a", float(i)) for i in range(8)] + [_entry("s1", "job_a", 500.0)]
    job_b = [_entry("s1", "job_b", 2.0) for _ in range(9)]
    result = detect_anomalies([], job_a + job_b, z_threshold=2.0)
    jobs_flagged = {a.job for a in result}
    assert "job_a" in jobs_flagged
    assert "job_b" not in jobs_flagged


def test_anomaly_label_late():
    a = Anomaly(server="s", job="j", drift=30.0, mean=5.0, stddev=3.0, z_score=2.5)
    assert "late" in a.label
    assert "s/j" in a.label


def test_anomaly_label_early():
    a = Anomaly(server="s", job="j", drift=-20.0, mean=0.0, stddev=5.0, z_score=-2.5)
    assert "early" in a.label


# --- format_anomalies ---

def test_format_anomalies_empty():
    assert format_anomalies([]) == "No anomalies detected."


def test_format_anomalies_shows_count():
    anomalies = [
        Anomaly(server="s", job="j", drift=50.0, mean=1.0, stddev=2.0, z_score=3.1)
    ]
    out = format_anomalies(anomalies)
    assert "1" in out
    assert "!!" in out
