"""Tests for sched_drift.replay."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from sched_drift.parser import LogEntry
from sched_drift.replay import replay, format_replay, ReplayResult
from sched_drift.schedule import ScheduleMatch


def _entry(
    server: str = "srv1",
    job: str = "backup",
    drift: float = 30.0,
    actual: datetime | None = None,
) -> LogEntry:
    if actual is None:
        actual = datetime(2024, 1, 15, 12, 0, 30, tzinfo=timezone.utc)
    scheduled = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return LogEntry(
        server=server,
        job=job,
        scheduled_time=scheduled,
        actual_time=actual,
        drift_seconds=drift,
    )


def _fake_match(drift: float) -> ScheduleMatch:
    m = MagicMock(spec=ScheduleMatch)
    m.drift_seconds = drift
    return m


def test_replay_returns_result_for_each_entry():
    entries = [_entry(), _entry(server="srv2", job="sync")]
    with patch("sched_drift.replay.match_schedule", return_value=_fake_match(10.0)):
        results = replay(entries, new_expr="*/5 * * * *")
    assert len(results) == 2


def test_replay_filters_by_server():
    entries = [_entry(server="srv1"), _entry(server="srv2")]
    with patch("sched_drift.replay.match_schedule", return_value=_fake_match(5.0)):
        results = replay(entries, new_expr="* * * * *", server="srv1")
    assert len(results) == 1
    assert results[0].entry.server == "srv1"


def test_replay_filters_by_job():
    entries = [_entry(job="backup"), _entry(job="sync")]
    with patch("sched_drift.replay.match_schedule", return_value=_fake_match(5.0)):
        results = replay(entries, new_expr="* * * * *", job="backup")
    assert len(results) == 1
    assert results[0].entry.job == "backup"


def test_replay_delta_computed_correctly():
    entry = _entry(drift=30.0)
    with patch("sched_drift.replay.match_schedule", return_value=_fake_match(10.0)):
        results = replay([entry], new_expr="* * * * *")
    assert results[0].delta == pytest.approx(10.0 - 30.0)


def test_replay_improved_when_abs_drift_reduced():
    entry = _entry(drift=60.0)
    with patch("sched_drift.replay.match_schedule", return_value=_fake_match(5.0)):
        results = replay([entry], new_expr="* * * * *")
    assert results[0].improved is True


def test_replay_not_improved_when_drift_increases():
    entry = _entry(drift=5.0)
    with patch("sched_drift.replay.match_schedule", return_value=_fake_match(60.0)):
        results = replay([entry], new_expr="* * * * *")
    assert results[0].improved is False


def test_replay_none_match_sets_delta_none():
    entry = _entry()
    with patch("sched_drift.replay.match_schedule", return_value=None):
        results = replay([entry], new_expr="invalid")
    assert results[0].delta is None
    assert results[0].improved is None


def test_format_replay_empty():
    assert format_replay([]) == "No replay results."


def test_format_replay_includes_server_and_job():
    entry = _entry(server="web01", job="cleanup", drift=20.0)
    match = _fake_match(5.0)
    result = ReplayResult(entry=entry, original_drift=20.0, replayed=match, delta=-15.0)
    output = format_replay([result])
    assert "web01" in output
    assert "cleanup" in output


def test_format_replay_limit_respected():
    entries = [_entry(server=f"s{i}") for i in range(10)]
    with patch("sched_drift.replay.match_schedule", return_value=_fake_match(1.0)):
        results = replay(entries, new_expr="* * * * *")
    output = format_replay(results, limit=3)
    # header + separator + 3 data rows
    assert output.count("\n") == 4
