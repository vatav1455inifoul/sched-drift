"""Tests for sched_drift.multi_log."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from sched_drift.multi_log import load_logs, load_logs_from_dir


LOG_A = textwrap.dedent("""\
    2024-01-10T08:00:05 server-a backup 2024-01-10T08:00:00
    2024-01-10T09:00:10 server-a cleanup 2024-01-10T09:00:00
""")

LOG_B = textwrap.dedent("""\
    2024-01-10T08:00:02 server-b backup 2024-01-10T08:00:00
    # this is a comment
    2024-01-10T10:00:00 server-b report 2024-01-10T10:00:00
""")


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    (tmp_path / "a.log").write_text(LOG_A)
    (tmp_path / "b.log").write_text(LOG_B)
    return tmp_path


def test_load_logs_merges_entries(log_dir: Path) -> None:
    paths = [str(log_dir / "a.log"), str(log_dir / "b.log")]
    result = load_logs(paths)
    assert len(result.entries) == 5
    assert result.errors == {}


def test_load_logs_servers_property(log_dir: Path) -> None:
    paths = [str(log_dir / "a.log"), str(log_dir / "b.log")]
    result = load_logs(paths)
    assert result.servers == ["server-a", "server-b"]


def test_load_logs_entries_for_server(log_dir: Path) -> None:
    paths = [str(log_dir / "a.log"), str(log_dir / "b.log")]
    result = load_logs(paths)
    assert len(result.entries_for_server("server-a")) == 2
    assert len(result.entries_for_server("server-b")) == 3


def test_load_logs_missing_file_recorded_in_errors() -> None:
    result = load_logs(["/nonexistent/path/file.log"])
    assert "/nonexistent/path/file.log" in result.errors
    assert result.entries == []


def test_load_logs_partial_failure(log_dir: Path) -> None:
    paths = [str(log_dir / "a.log"), "/no/such/file.log"]
    result = load_logs(paths)
    assert len(result.entries) == 2
    assert "/no/such/file.log" in result.errors


def test_load_logs_from_dir_discovers_files(log_dir: Path) -> None:
    result = load_logs_from_dir(str(log_dir))
    assert len(result.entries) == 5
    assert result.errors == {}


def test_load_logs_from_dir_bad_directory() -> None:
    result = load_logs_from_dir("/nonexistent/dir")
    assert "/nonexistent/dir" in result.errors
    assert result.entries == []


def test_load_logs_from_dir_custom_pattern(log_dir: Path) -> None:
    (log_dir / "notes.txt").write_text("not a log")
    result = load_logs_from_dir(str(log_dir), pattern="*.log")
    # only .log files should be picked up
    assert result.errors == {}
    assert len(result.entries) == 5
