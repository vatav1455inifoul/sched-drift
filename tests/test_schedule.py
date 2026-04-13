"""Tests for sched_drift.schedule."""

from datetime import datetime

import pytest

pytest.importorskip("croniter", reason="croniter not installed")

from sched_drift.schedule import ScheduleMatch, match_schedule, nearest_expected


# ---------------------------------------------------------------------------
# nearest_expected
# ---------------------------------------------------------------------------

def test_nearest_expected_returns_datetime():
    # Every minute — nearest tick to :30 should be either :00 or :01
    actual = datetime(2024, 1, 15, 12, 0, 30)
    result = nearest_expected("* * * * *", actual)
    assert isinstance(result, datetime)


def test_nearest_expected_exact_tick():
    # Actual is exactly on a scheduled minute boundary
    actual = datetime(2024, 1, 15, 12, 5, 0)
    result = nearest_expected("*/5 * * * *", actual)
    assert result is not None
    assert result == actual


def test_nearest_expected_invalid_expr_returns_none():
    actual = datetime(2024, 1, 15, 12, 0, 0)
    result = nearest_expected("not a cron", actual)
    assert result is None


# ---------------------------------------------------------------------------
# match_schedule
# ---------------------------------------------------------------------------

def test_match_schedule_returns_schedule_match():
    actual = datetime(2024, 1, 15, 12, 0, 10)
    result = match_schedule("* * * * *", actual)
    assert isinstance(result, ScheduleMatch)


def test_match_schedule_drift_late():
    # Job ran 45 seconds after the top of the minute
    actual = datetime(2024, 1, 15, 12, 0, 45)
    result = match_schedule("0 12 * * *", actual)  # daily at 12:00
    assert result is not None
    assert result.drift_seconds == pytest.approx(45.0)
    assert result.is_late
    assert not result.is_early


def test_match_schedule_drift_early():
    # Job ran 20 seconds before the scheduled minute
    actual = datetime(2024, 1, 15, 11, 59, 40)
    result = match_schedule("0 12 * * *", actual)
    assert result.drift_seconds == pytest.approx(-20.0)
    assert result.is_early
    assert not result.is_late


def test_match_schedule_on_time():
    actual = datetime(2024, 1, 15, 12, 0, 0)
    result = match_schedule("0 12n    assert result is not None
    assert result.drift_seconds == pytest.approx(0.0)
    assert not result.is_late
    assert not result.is_early


def test_match_schedule_invalid_expr_returns_none():
    actual = datetime(2024, 1, 15, 12, 0, 0)
    assert match_schedule("bad expr", actual) is None


def test_match_schedule_stores_cron_expr():
    actual = datetime(2024, 1, 15, 9, 0, 5)
    expr = "0 9 * * *"
    result = match_schedule(expr, actual)
    assert result is not None
    assert result.cron_expr == expr
