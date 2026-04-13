"""Top-N drift offenders: find jobs/servers with highest average drift."""

from dataclasses import dataclass
from typing import List, Optional
from sched_drift.reporter import DriftReport


@dataclass
class TopEntry:
    server: str
    job: str
    avg_drift: float
    max_drift: float
    count: int


def _abs_avg(report: DriftReport) -> float:
    return abs(report.summary.avg_drift)


def top_n(
    reports: List[DriftReport],
    n: int = 5,
    server: Optional[str] = None,
    by_max: bool = False,
) -> List[TopEntry]:
    """Return the top-N entries sorted by absolute avg drift (or max drift)."""
    filtered = reports
    if server:
        filtered = [r for r in reports if r.server == server]

    def sort_key(r: DriftReport) -> float:
        if by_max:
            return abs(r.summary.max_drift)
        return abs(r.summary.avg_drift)

    ranked = sorted(filtered, key=sort_key, reverse=True)
    return [
        TopEntry(
            server=r.server,
            job=r.job,
            avg_drift=r.summary.avg_drift,
            max_drift=r.summary.max_drift,
            count=r.summary.count,
        )
        for r in ranked[:n]
    ]


def format_topn(entries: List[TopEntry], by_max: bool = False) -> str:
    """Format top-N entries as a human-readable table."""
    if not entries:
        return "No drift data available."

    sort_label = "max drift" if by_max else "avg drift"
    lines = [f"Top offenders by {sort_label}:", ""]
    header = f"  {'#':<4} {'server':<20} {'job':<25} {'avg (s)':>10} {'max (s)':>10} {'count':>6}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))

    for i, e in enumerate(entries, start=1):
        lines.append(
            f"  {i:<4} {e.server:<20} {e.job:<25} {e.avg_drift:>+10.1f} {e.max_drift:>+10.1f} {e.count:>6}"
        )

    return "\n".join(lines)
