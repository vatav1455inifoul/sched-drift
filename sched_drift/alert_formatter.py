"""Format alerts for CLI output."""

from typing import List
from sched_drift.alerts import Alert

SEVERITY_PREFIX = {
    "warning": "[WARN] ",
    "critical": "[CRIT] ",
}


def format_alerts(alerts: List[Alert], use_color: bool = False) -> str:
    """Render a list of alerts as a human-readable string."""
    if not alerts:
        return "No alerts triggered."

    color_map = {
        "warning": "\033[33m",   # yellow
        "critical": "\033[31m",  # red
        "reset": "\033[0m",
    }

    lines = [f"Alerts ({len(alerts)} triggered):", ""]
    for alert in alerts:
        prefix = SEVERITY_PREFIX.get(alert.severity, "[INFO] ")
        line = (
            f"{prefix}{alert.server} / {alert.job} "
            f"[{alert.rule_name}]: {alert.message}"
        )
        if use_color:
            color = color_map.get(alert.severity, "")
            line = f"{color}{line}{color_map['reset']}"
        lines.append(line)

    return "\n".join(lines)


def alerts_by_severity(alerts: List[Alert]) -> dict:
    """Group alerts into a dict keyed by severity."""
    grouped: dict = {}
    for alert in alerts:
        grouped.setdefault(alert.severity, []).append(alert)
    return grouped


def has_critical(alerts: List[Alert]) -> bool:
    """Return True if any alert is critical severity."""
    return any(a.severity == "critical" for a in alerts)
