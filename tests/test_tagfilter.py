"""Tests for sched_drift.tagfilter."""
from __future__ import annotations

import datetime

import pytest

from sched_drift.parser import LogEntry
from sched_drift.reporter import DriftReport
from sched_drift.tagfilter import (
    TagFilter,
    filter_entries,
    filter_reports,
    format_tag_summary,
)


def _entry(job: str, server: str = "web-01") -> LogEntry:
    t = datetime.datetime(2024, 1, 1, 12, 0, 0)
    return LogEntry(server=server, job_name=job, scheduled_time=t, actual_time=t)


def _report(job: str, server: str = "web-01") -> DriftReport:
    return DriftReport(
        server=server,
        job_name=job,
        avg_drift=0.0,
        max_drift=0.0,
        min_drift=0.0,
        late_count=0,
        early_count=0,
        on_time_count=1,
        entries=[_entry(job, server)],
    )


# --- TagFilter.matches ---

def test_matches_no_tags_accepts_all():
    tf = TagFilter()
    assert tf.matches(_entry("backup")) is True


def test_matches_tag_substring():
    tf = TagFilter(tags=["back"])
    assert tf.matches(_entry("backup-daily")) is True


def test_no_match_when_tag_absent():
    tf = TagFilter(tags=["report"])
    assert tf.matches(_entry("backup-daily")) is False


def test_exclude_overrides_include():
    tf = TagFilter(tags=["backup"], exclude=["daily"])
    assert tf.matches(_entry("backup-daily")) is False


def test_exclude_only_removes_matching():
    tf = TagFilter(exclude=["test"])
    assert tf.matches(_entry("backup")) is True
    assert tf.matches(_entry("test-job")) is False


def test_case_insensitive_matching():
    tf = TagFilter(tags=["BACKUP"])
    assert tf.matches(_entry("Backup-Daily")) is True


# --- filter_entries ---

def test_filter_entries_keeps_matching():
    entries = [_entry("backup"), _entry("report"), _entry("backup-weekly")]
    result = filter_entries(entries, TagFilter(tags=["backup"]))
    assert len(result) == 2
    assert all("backup" in e.job_name for e in result)


def test_filter_entries_empty_list():
    assert filter_entries([], TagFilter(tags=["backup"])) == []


# --- filter_reports ---

def test_filter_reports_keeps_matching():
    reports = [_report("backup"), _report("report-gen"), _report("backup-monthly")]
    result = filter_reports(reports, TagFilter(tags=["backup"]))
    assert len(result) == 2


def test_filter_reports_with_exclude():
    reports = [_report("backup-daily"), _report("backup-weekly"), _report("report")]
    result = filter_reports(reports, TagFilter(tags=["backup"], exclude=["weekly"]))
    assert len(result) == 1
    assert result[0].job_name == "backup-daily"


# --- format_tag_summary ---

def test_format_tag_summary_contains_counts():
    summary = format_tag_summary(3, 10, TagFilter(tags=["backup"]))
    assert "3/10" in summary


def test_format_tag_summary_shows_tags():
    summary = format_tag_summary(1, 5, TagFilter(tags=["backup", "sync"]))
    assert "backup" in summary
    assert "sync" in summary


def test_format_tag_summary_no_tags_shows_all():
    summary = format_tag_summary(5, 5, TagFilter())
    assert "(all)" in summary
