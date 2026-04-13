"""Generates drift reports from parsed log entries."""

from dataclasses import dataclass
from typing import List, Optional
from sched_drift.parser import LogEntry, drift_seconds


@dataclass
class DriftReport:
    job_name: str
    server: str
    total_runs: int
    avg_drift_seconds: float
    max_drift_seconds: float
    min_drift_seconds: float
    late_runs: int
    early_runs: int
    on_time_runs: int

    def summary(self) -> str:
        direction = "late" if self.avg_drift_seconds > 0 else "early"
        return (
            f"[{self.server}] {self.job_name}: "
            f"{self.total_runs} runs, "
            f"avg {abs(self.avg_drift_seconds):.1f}s {direction}, "
            f"max drift {self.max_drift_seconds:.1f}s"
        )


def build_report(entries: List[LogEntry], server: Optional[str] = None) -> List[DriftReport]:
    """Build drift reports grouped by server + job name."""
    groups: dict = {}

    for entry in entries:
        key = (entry.server, entry.job_name)
        if key not in groups:
            groups[key] = []
        groups[key].append(entry)

    reports = []
    for (srv, job), group in groups.items():
        if server and srv != server:
            continue

        drifts = [drift_seconds(e) for e in group]
        late = sum(1 for d in drifts if d > 0)
        early = sum(1 for d in drifts if d < 0)
        on_time = sum(1 for d in drifts if d == 0)

        reports.append(
            DriftReport(
                job_name=job,
                server=srv,
                total_runs=len(drifts),
                avg_drift_seconds=sum(drifts) / len(drifts),
                max_drift_seconds=max(drifts),
                min_drift_seconds=min(drifts),
                late_runs=late,
                early_runs=early,
                on_time_runs=on_time,
            )
        )

    return sorted(reports, key=lambda r: abs(r.avg_drift_seconds), reverse=True)


def format_report(reports: List[DriftReport], verbose: bool = False) -> str:
    """Format a list of DriftReports into a human-readable string."""
    if not reports:
        return "No drift data found."

    lines = ["=== Cron Drift Report ==="]
    for r in reports:
        lines.append(r.summary())
        if verbose:
            lines.append(
                f"  late={r.late_runs} early={r.early_runs} "
                f"on_time={r.on_time_runs} "
                f"min={r.min_drift_seconds:.1f}s max={r.max_drift_seconds:.1f}s"
            )
    return "\n".join(lines)
