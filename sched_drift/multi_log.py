"""Utilities for loading and merging log files from multiple servers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from sched_drift.parser import LogEntry, parse_log_file


@dataclass
class MultiLogResult:
    """Aggregated entries from multiple log files, keyed by server name."""

    entries: List[LogEntry] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    @property
    def servers(self) -> List[str]:
        return sorted({e.server for e in self.entries})

    def entries_for_server(self, server: str) -> List[LogEntry]:
        return [e for e in self.entries if e.server == server]


def _server_name_from_path(path: Path, use_filename: bool = True) -> Optional[str]:
    """Derive a server name from a file path.

    If *use_filename* is True the stem of the file is used as a fallback when
    the log lines themselves do not carry a server field.  In practice the
    parser already reads the server from each line, so this is informational.
    """
    return path.stem if use_filename else None


def load_logs(paths: List[str]) -> MultiLogResult:
    """Parse a list of log file paths and merge all entries.

    Files that cannot be read are recorded in *errors* rather than raising.
    """
    result = MultiLogResult()

    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            result.errors[raw_path] = "file not found"
            continue
        if not os.access(path, os.R_OK):
            result.errors[raw_path] = "permission denied"
            continue
        try:
            entries = parse_log_file(str(path))
            result.entries.extend(entries)
        except Exception as exc:  # noqa: BLE001
            result.errors[raw_path] = str(exc)

    return result


def load_logs_from_dir(directory: str, pattern: str = "*.log") -> MultiLogResult:
    """Recursively discover log files in *directory* matching *pattern*."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        result = MultiLogResult()
        result.errors[directory] = "not a directory"
        return result

    paths = sorted(str(p) for p in dir_path.rglob(pattern))
    return load_logs(paths)
