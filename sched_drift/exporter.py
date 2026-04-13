"""Export drift reports to various output formats (JSON, CSV)."""

import csv
import json
import io
from typing import List
from sched_drift.reporter import DriftReport


def report_to_dict(report: DriftReport) -> dict:
    """Convert a DriftReport to a plain dictionary."""
    return {
        "server": report.server,
        "job": report.job,
        "summary": {
            "avg_drift_seconds": round(report.summary.avg_drift, 2),
            "max_drift_seconds": round(report.summary.max_drift, 2),
            "min_drift_seconds": round(report.summary.min_drift, 2),
            "late_count": report.summary.late_count,
            "early_count": report.summary.early_count,
            "total_runs": report.summary.total_runs,
        },
    }


def export_json(reports: List[DriftReport], indent: int = 2) -> str:
    """Serialize a list of DriftReports to a JSON string."""
    data = [report_to_dict(r) for r in reports]
    return json.dumps(data, indent=indent)


def export_csv(reports: List[DriftReport]) -> str:
    """Serialize a list of DriftReports to a CSV string."""
    fieldnames = [
        "server",
        "job",
        "avg_drift_seconds",
        "max_drift_seconds",
        "min_drift_seconds",
        "late_count",
        "early_count",
        "total_runs",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for report in reports:
        d = report_to_dict(report)
        writer.writerow({
            "server": d["server"],
            "job": d["job"],
            **d["summary"],
        })
    return output.getvalue()
