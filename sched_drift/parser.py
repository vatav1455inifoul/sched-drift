"""Parser for cron log entries — extracts scheduled and actual execution times."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Expected log format:
# 2024-01-15T14:30:05Z [server-01] job=backup_db scheduled=2024-01-15T14:30:00Z
LOG_PATTERN = re.compile(
    r"(?P<actual>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+"
    r"\[(?P<server>[^\]]+)\]\s+"
    r"job=(?P<job>\S+)\s+"
    r"scheduled=(?P<scheduled>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"
)

DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class LogEntry:
    server: str
    job: str
    scheduled: datetime
    actual: datetime

    @property
    def drift_seconds(self) -> float:
        """Return drift in seconds (positive = late, negative = early)."""
        return (self.actual - self.scheduled).total_seconds()


def parse_line(line: str) -> Optional[LogEntry]:
    """Parse a single log line into a LogEntry, or return None if it doesn't match."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    match = LOG_PATTERN.search(line)
    if not match:
        return None

    return LogEntry(
        server=match.group("server"),
        job=match.group("job"),
        scheduled=datetime.strptime(match.group("scheduled"), DATETIME_FMT),
        actual=datetime.strptime(match.group("actual"), DATETIME_FMT),
    )


def parse_log_file(filepath: str) -> list[LogEntry]:
    """Parse all valid entries from a log file."""
    entries = []
    with open(filepath, "r") as f:
        for line in f:
            entry = parse_line(line)
            if entry is not None:
                entries.append(entry)
    return entries
