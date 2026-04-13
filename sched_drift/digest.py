"""Digest module: produce a human-readable summary digest of drift reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sched_drift.reporter import DriftReport


@dataclass
class DigestLine:
    server: str
    job: str
    avg_drift: float
    max_drift: float
    occurrences: int
    status: str  # 'ok' | 'warn' | 'critical'


def _status(avg_drift: float, warn: float = 60.0, critical: float = 300.0) -> str:
    abs_avg = abs(avg_drift)
    if abs_avg >= critical:
        return "critical"
    if abs_avg >= warn:
        return "warn"
    return "ok"


def build_digest(
    reports: List[DriftReport],
    warn_threshold: float = 60.0,
    critical_threshold: float = 300.0,
) -> List[DigestLine]:
    """Convert a list of DriftReports into DigestLines sorted by abs avg drift desc."""
    lines: List[DigestLine] = []
    for r in reports:
        s = _status(r.avg_drift, warn_threshold, critical_threshold)
        max_d = max((abs(e.drift) for e in r.entries), default=0.0)
        lines.append(
            DigestLine(
                server=r.server,
                job=r.job,
                avg_drift=round(r.avg_drift, 2),
                max_drift=round(max_d, 2),
                occurrences=len(r.entries),
                status=s,
            )
        )
    lines.sort(key=lambda l: abs(l.avg_drift), reverse=True)
    return lines


def format_digest(lines: List[DigestLine]) -> str:
    """Render digest lines as a plain-text table."""
    if not lines:
        return "No drift data available."

    header = f"{'SERVER':<20} {'JOB':<25} {'AVG DRIFT':>10} {'MAX DRIFT':>10} {'COUNT':>6} {'STATUS':<10}"
    sep = "-" * len(header)
    rows = [header, sep]
    for dl in lines:
        status_tag = {"ok": "[ OK ]", "warn": "[WARN]", "critical": "[CRIT]"}[dl.status]
        rows.append(
            f"{dl.server:<20} {dl.job:<25} {dl.avg_drift:>10.1f} {dl.max_drift:>10.1f} {dl.occurrences:>6} {status_tag:<10}"
        )
    rows.append(sep)
    ok = sum(1 for l in lines if l.status == "ok")
    warn = sum(1 for l in lines if l.status == "warn")
    crit = sum(1 for l in lines if l.status == "critical")
    rows.append(f"Summary: {len(lines)} job(s) — {ok} ok, {warn} warn, {crit} critical")
    return "\n".join(rows)
