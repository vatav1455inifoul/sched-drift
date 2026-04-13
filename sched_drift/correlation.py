"""Correlate drift patterns across servers to detect systemic vs isolated issues."""

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from sched_drift.reporter import DriftReport


@dataclass
class CorrelationResult:
    job: str
    servers: List[str]
    avg_drifts: Dict[str, float]
    is_systemic: bool  # True if all servers show similar drift direction
    spread: float      # max avg drift - min avg drift in seconds


def _same_direction(values: List[float]) -> bool:
    """Return True if all non-zero values share the same sign."""
    signs = [v > 0 for v in values if abs(v) > 1]
    return len(signs) > 1 and (all(signs) or not any(signs))


def correlate(reports: List[DriftReport], spread_threshold: float = 30.0) -> List[CorrelationResult]:
    """Group reports by job and compare drift across servers."""
    by_job: Dict[str, Dict[str, float]] = defaultdict(dict)

    for r in reports:
        by_job[r.job][r.server] = r.avg_drift

    results: List[CorrelationResult] = []
    for job, server_drifts in by_job.items():
        if len(server_drifts) < 2:
            continue
        servers = list(server_drifts.keys())
        avg_drifts = dict(server_drifts)
        values = list(avg_drifts.values())
        spread = max(values) - min(values)
        systemic = _same_direction(values) and spread <= spread_threshold
        results.append(CorrelationResult(
            job=job,
            servers=servers,
            avg_drifts=avg_drifts,
            is_systemic=systemic,
            spread=round(spread, 2),
        ))

    results.sort(key=lambda r: r.job)
    return results


def format_correlation(results: List[CorrelationResult]) -> str:
    """Return a human-readable summary of correlation results."""
    if not results:
        return "No cross-server correlations found (need >=2 servers per job)."

    lines = ["Cross-Server Drift Correlation", "=" * 34]
    for r in results:
        tag = "[SYSTEMIC]" if r.is_systemic else "[ISOLATED]"
        lines.append(f"\nJob: {r.job}  {tag}  spread={r.spread:.1f}s")
        for srv in sorted(r.servers):
            drift = r.avg_drifts[srv]
            sign = "+" if drift >= 0 else ""
            lines.append(f"  {srv}: avg drift {sign}{drift:.1f}s")

    return "\n".join(lines)
