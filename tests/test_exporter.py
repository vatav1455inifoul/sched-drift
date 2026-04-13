"""Tests for sched_drift.exporter."""

import json
import csv
import io
import pytest
from sched_drift.parser import LogEntry
from sched_drift.reporter import build_report
from sched_drift.exporter import export_json, export_csv, report_to_dict


def _make_entry(server: str, job: str, drift: float) -> LogEntry:
    from datetime import datetime, timezone
    scheduled = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
    actual = datetime(2024, 1, 1, 6, 0, int(abs(drift)), tzinfo=timezone.utc)
    if drift < 0:
        actual = datetime(2024, 1, 1, 5, 59, 60 - int(abs(drift)), tzinfo=timezone.utc)
    return LogEntry(server=server, job=job, scheduled=scheduled, actual=actual)


def _reports():
    entries = [
        _make_entry("web-01", "backup", 30),
        _make_entry("web-01", "backup", 60),
        _make_entry("db-01", "vacuum", -10),
    ]
    return build_report(entries)


def test_report_to_dict_keys():
    reports = _reports()
    d = report_to_dict(reports[0])
    assert "server" in d
    assert "job" in d
    assert "summary" in d
    summary_keys = {"avg_drift_seconds", "max_drift_seconds", "min_drift_seconds",
                    "late_count", "early_count", "total_runs"}
    assert summary_keys == set(d["summary"].keys())


def test_export_json_is_valid():
    reports = _reports()
    result = export_json(reports)
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == len(reports)


def test_export_json_contains_server_and_job():
    reports = _reports()
    parsed = json.loads(export_json(reports))
    servers = {r["server"] for r in parsed}
    assert "web-01" in servers
    assert "db-01" in servers


def test_export_csv_has_header():
    reports = _reports()
    result = export_csv(reports)
    reader = csv.DictReader(io.StringIO(result))
    assert "server" in reader.fieldnames
    assert "avg_drift_seconds" in reader.fieldnames


def test_export_csv_row_count():
    reports = _reports()
    result = export_csv(reports)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == len(reports)


def test_export_csv_values():
    reports = _reports()
    result = export_csv(reports)
    reader = csv.DictReader(io.StringIO(result))
    rows = {(r["server"], r["job"]): r for r in reader}
    assert ("db-01", "vacuum") in rows
    assert int(rows[("db-01", "vacuum")]["total_runs"]) == 1
