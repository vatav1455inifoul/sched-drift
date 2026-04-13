"""Tests for sched_drift.groupby."""

from datetime import datetime

import pytest

from sched_drift.groupby import (
    GroupBucket,
    format_groupby,
    group_by_window,
)
from sched_drift.parser import LogEntry


def _entry(actual: datetime, drift: float) -> LogEntry:
    return LogEntry(
        server="srv1",
        job="backup",
        scheduled_time=actual,
        actual_time=actual,
        drift=drift,
    )


SAMPLE = [
    _entry(datetime(2024, 3, 4, 8, 0), 10.0),   # Mon 08:00
    _entry(datetime(2024, 3, 4, 8, 30), 20.0),  # Mon 08:00
    _entry(datetime(2024, 3, 4, 14, 0), -5.0),  # Mon 14:00
    _entry(datetime(2024, 3, 5, 8, 0), 30.0),   # Tue 08:00
]


def test_group_by_hour_creates_correct_buckets():
    buckets = group_by_window(SAMPLE, window="hour")
    labels = [b.label for b in buckets]
    assert "08:00" in labels
    assert "14:00" in labels


def test_group_by_hour_count():
    buckets = group_by_window(SAMPLE, window="hour")
    by_label = {b.label: b for b in buckets}
    assert by_label["08:00"].count == 3
    assert by_label["14:00"].count == 1


def test_group_by_hour_avg_drift():
    buckets = group_by_window(SAMPLE, window="hour")
    by_label = {b.label: b for b in buckets}
    assert by_label["08:00"].avg_drift == pytest.approx(20.0)
    assert by_label["14:00"].avg_drift == pytest.approx(-5.0)


def test_group_by_day_labels():
    buckets = group_by_window(SAMPLE, window="day")
    labels = [b.label for b in buckets]
    assert "2024-03-04" in labels
    assert "2024-03-05" in labels


def test_group_by_weekday_labels():
    buckets = group_by_window(SAMPLE, window="weekday")
    labels = [b.label for b in buckets]
    assert "Mon" in labels
    assert "Tue" in labels


def test_group_by_weekday_mon_count():
    buckets = group_by_window(SAMPLE, window="weekday")
    by_label = {b.label: b for b in buckets}
    assert by_label["Mon"].count == 3


def test_group_by_empty_returns_empty():
    assert group_by_window([], window="hour") == []


def test_unknown_window_raises():
    with pytest.raises(ValueError, match="Unknown window"):
        group_by_window(SAMPLE, window="minute")  # type: ignore[arg-type]


def test_format_groupby_empty():
    result = format_groupby([], window="hour")
    assert "No data" in result


def test_format_groupby_includes_label():
    buckets = group_by_window(SAMPLE, window="hour")
    output = format_groupby(buckets, window="hour")
    assert "08:00" in output
    assert "14:00" in output


def test_format_groupby_shows_window_name():
    buckets = group_by_window(SAMPLE, window="day")
    output = format_groupby(buckets, window="day")
    assert "day" in output
