"""Tests for sched_drift.normalize."""

from datetime import datetime
from sched_drift.parser import LogEntry
from sched_drift.normalize import (
    normalize_entries,
    format_normalized,
    NormalizedEntry,
)


def _entry(server: str, job: str, drift: int) -> LogEntry:
    scheduled = datetime(2024, 1, 1, 12, 0, 0)
    actual = datetime(2024, 1, 1, 12, 0, drift) if drift >= 0 else datetime(2024, 1, 1, 11, 59, 60 + drift)
    return LogEntry(server=server, job=job, scheduled=scheduled, actual=actual)


def test_normalize_empty_returns_empty():
    assert normalize_entries([]) == []


def test_normalize_single_entry_returns_half():
    entries = [_entry("srv1", "backup", 30)]
    result = normalize_entries(entries)
    assert len(result) == 1
    assert result[0].normalized == 0.5


def test_normalize_two_entries_span_zero_to_one():
    entries = [_entry("srv1", "backup", 0), _entry("srv2", "backup", 60)]
    result = normalize_entries(entries)
    norms = sorted(r.normalized for r in result)
    assert norms[0] == 0.0
    assert norms[1] == 1.0


def test_normalize_preserves_raw_drift():
    entries = [_entry("srv1", "job", 10), _entry("srv2", "job", 50)]
    result = normalize_entries(entries)
    raw = {r.server: r.raw_drift for r in result}
    assert raw["srv1"] == 10.0
    assert raw["srv2"] == 50.0


def test_normalize_z_score_none_for_single_entry():
    entries = [_entry("srv1", "job", 20)]
    result = normalize_entries(entries)
    assert result[0].z_score is None


def test_normalize_z_score_none_when_all_same():
    entries = [_entry("srv1", "job", 30), _entry("srv2", "job", 30)]
    result = normalize_entries(entries)
    for r in result:
        assert r.z_score is None


def test_normalize_z_score_outlier_has_high_absolute_value():
    entries = [
        _entry("s1", "j", 0),
        _entry("s2", "j", 0),
        _entry("s3", "j", 0),
        _entry("s4", "j", 120),
    ]
    result = normalize_entries(entries)
    outlier = next(r for r in result if r.server == "s4")
    assert outlier.z_score is not None
    assert abs(outlier.z_score) > 1.0


def test_format_normalized_empty():
    out = format_normalized([])
    assert "No entries" in out


def test_format_normalized_contains_server_and_job():
    entries = [_entry("web01", "cleanup", 15)]
    result = normalize_entries(entries)
    out = format_normalized(result)
    assert "web01" in out
    assert "cleanup" in out


def test_format_normalized_shows_header():
    entries = [_entry("srv", "job", 5)]
    result = normalize_entries(entries)
    out = format_normalized(result)
    assert "SERVER" in out
    assert "NORM" in out
    assert "Z-SCORE" in out
