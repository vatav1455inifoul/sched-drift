"""Tests for sched_drift.rankby."""
from datetime import datetime
from sched_drift.parser import LogEntry
from sched_drift.reporter import build_report
from sched_drift.rankby import rank_reports, format_rankby, RankEntry


def _entry(server: str, job: str, drift: int) -> LogEntry:
    now = datetime(2024, 1, 1, 12, 0, 0)
    return LogEntry(
        server=server,
        job=job,
        scheduled_time=now,
        actual_time=now,
        drift_seconds=drift,
    )


def _reports(entries):
    return build_report(entries)


def test_rank_returns_correct_count():
    entries = [
        _entry("s1", "job_a", 120),
        _entry("s2", "job_b", 300),
        _entry("s3", "job_c", 60),
    ]
    result = rank_reports(_reports(entries), metric="avg_drift", top=2)
    assert len(result) == 2


def test_rank_sorted_descending_by_default():
    entries = [
        _entry("s1", "job_a", 10),
        _entry("s2", "job_b", 500),
        _entry("s3", "job_c", 200),
    ]
    result = rank_reports(_reports(entries), metric="avg_drift", top=3)
    assert result[0].value >= result[1].value >= result[2].value


def test_rank_ascending():
    entries = [
        _entry("s1", "job_a", 10),
        _entry("s2", "job_b", 500),
        _entry("s3", "job_c", 200),
    ]
    result = rank_reports(_reports(entries), metric="avg_drift", top=3, ascending=True)
    assert result[0].value <= result[1].value <= result[2].value


def test_rank_numbers_start_at_one():
    entries = [_entry("s1", "job_a", 100), _entry("s2", "job_b", 50)]
    result = rank_reports(_reports(entries), metric="avg_drift")
    assert result[0].rank == 1
    assert result[1].rank == 2


def test_group_by_server_merges_jobs():
    entries = [
        _entry("srv", "job_a", 100),
        _entry("srv", "job_b", 200),
        _entry("other", "job_a", 50),
    ]
    result = rank_reports(_reports(entries), metric="avg_drift", group_by="server", top=5)
    keys = [r.key for r in result]
    assert "srv" in keys
    assert "other" in keys
    # srv should be ranked first (avg of 100+200 vs 50)
    assert result[0].key == "srv"


def test_late_count_metric():
    entries = [
        _entry("s1", "job_a", 90),   # late
        _entry("s1", "job_a", 90),   # late
        _entry("s2", "job_b", -30),  # early
    ]
    result = rank_reports(_reports(entries), metric="late_count", top=5)
    top = next(r for r in result if r.key == "s1/job_a")
    assert top.value == 2.0


def test_format_rankby_empty():
    assert format_rankby([], "avg_drift") == "No data to rank."


def test_format_rankby_contains_key():
    entry = RankEntry(rank=1, key="srv/job", metric="avg_drift", value=42.0)
    output = format_rankby([entry], "avg_drift")
    assert "srv/job" in output
    assert "42.0" in output
    assert "Avg Drift" in output
