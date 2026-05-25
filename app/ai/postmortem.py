from __future__ import annotations

from app.models import Incident, IncidentLinks, TimelineEvent


async def generate_postmortem(
    incident: Incident,
    timeline: list[TimelineEvent],
    links: IncidentLinks,
    resolution_summary: str | None = None,
) -> str:
    timeline_lines = "\n".join(
        f"- {event.timestamp.isoformat()}: {event.summary}" for event in timeline
    )
    service = ", ".join(incident.affected_services) or "unknown"
    symptoms = ", ".join(incident.symptoms) or "reported impact"
    link_lines = "\n".join(
        f"- {name}: {url}"
        for name, url in {
            "Jira": links.jira_url,
            "Slack": links.slack_channel_url,
            "Confluence": links.confluence_url,
            "PagerDuty": links.pagerduty_url,
            "Dashboard": links.dashboard_url,
        }.items()
        if url
    )
    return f"""# Incident Postmortem

## Summary
{incident.severity} incident for {service}: {incident.title}.

## Impact
Users experienced {symptoms}. Impact details require human review.

## Detection
Reported via IncidentForge command: {incident.original_message}

## Timeline
{timeline_lines or "- No timeline events recorded."}

## Response
IncidentForge coordinated Jira, Slack, Confluence, alerting, reminders, and timeline logging where configured.

## Resolution
{resolution_summary or "Resolution details pending human review."}

## Root Cause
Root cause pending investigation.

## What Went Well
- Incident workflow was started from one command.
- Actions and failures were captured in the timeline.

## What Went Wrong
- Needs human review for root cause and exact customer impact.

## Action Items
- Confirm root cause.
- Add preventive monitoring or runbook updates.
- Review response timing and ownership.

## Links
{link_lines or "- No external links recorded."}
"""
