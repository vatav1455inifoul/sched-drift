"""Rank servers or jobs by a chosen drift metric."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Dict

from sched_drift.reporter import DriftReport

RankMetric = Literal["avg_drift", "max_drift", "late_count", "early_count"]


@dataclass
class RankEntry:
    rank: int
    key: str          # server, job, or "server/job"
    metric: RankMetric
    value: float


def _key_for(report: DriftReport, group_by: str) -> str:
    if group_by == "server":
        return report.server
    if group_by == "job":
        return report.job
    return f"{report.server}/{report.job}"


def _value_for(report: DriftReport, metric: RankMetric) -> float:
    s = report.summary
    if metric == "avg_drift":
        return abs(s.avg_drift)
    if metric == "max_drift":
        return abs(s.max_drift)
    if metric == "late_count":
        return float(s.late_count)
    if metric == "early_count":
        return float(s.early_count)
    return 0.0


def rank_reports(
    reports: List[DriftReport],
    metric: RankMetric = "avg_drift",
    group_by: str = "server/job",
    top: int = 10,
    ascending: bool = False,
) -> List[RankEntry]:
    """Aggregate reports by *group_by* key then rank by *metric*."""
    buckets: Dict[str, List[float]] = {}
    for r in reports:
        key = _key_for(r, group_by)
        buckets.setdefault(key, []).append(_value_for(r, metric))

    aggregated = [
        (key, sum(vals) / len(vals)) for key, vals in buckets.items()
    ]
    aggregated.sort(key=lambda t: t[1], reverse=not ascending)
    aggregated = aggregated[:top]

    return [
        RankEntry(rank=i + 1, key=key, metric=metric, value=round(value, 2))
        for i, (key, value) in enumerate(aggregated)
    ]


def format_rankby(entries: List[RankEntry], metric: RankMetric) -> str:
    if not entries:
        return "No data to rank."
    label = metric.replace("_", " ").title()
    lines = [f"Rank  {'Key':<35}  {label}"]
    lines.append("-" * 60)
    for e in entries:
        lines.append(f"{e.rank:<5} {e.key:<35}  {e.value}")
    return "\n".join(lines)
