from __future__ import annotations

from app.models import Incident, IncidentLinks, TimelineEvent


async def summarize_status(
    incident: Incident,
    timeline: list[TimelineEvent],
    links: IncidentLinks,
) -> str:
    completed = [event.summary for event in timeline if event.type.endswith("_created") or event.type.endswith("_triggered")]
    blockers = [event.summary for event in timeline if event.type.endswith("_failed")]
    next_update = "not scheduled"
    for event in timeline:
        if event.type == "reminder_scheduled":
            next_update = event.summary
    services = ", ".join(incident.affected_services) or "unknown"
    lines = [
        f"Status: {incident.status.upper()} | Severity: {incident.severity} | Service: {services}",
        f"Incident: {incident.title}",
        "Completed: " + ("; ".join(completed) if completed else "No tool actions completed yet."),
        "Next update: " + next_update,
        "Blockers: " + ("; ".join(blockers) if blockers else "None logged."),
    ]
    link_bits = [
        f"Jira: {links.jira_url}" if links.jira_url else "",
        f"Slack: {links.slack_channel_url}" if links.slack_channel_url else "",
        f"Confluence: {links.confluence_url}" if links.confluence_url else "",
        f"Dashboard: {links.dashboard_url}" if links.dashboard_url else "",
    ]
    link_text = " | ".join(bit for bit in link_bits if bit)
    if link_text:
        lines.append(link_text)
    return "\n".join(lines)
