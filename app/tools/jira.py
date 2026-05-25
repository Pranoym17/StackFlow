from __future__ import annotations

import base64

import httpx

from app.config import Settings, get_settings
from app.models import Incident, ToolResult


PRIORITY_MAP = {"P0": "Highest", "P1": "High", "P2": "Medium", "P3": "Low"}


async def create_jira_issue(incident: Incident, settings: Settings | None = None) -> ToolResult:
    settings = settings or get_settings()
    if settings.demo_mode or not settings.jira_configured:
        key = f"{settings.jira_project_key}-{abs(hash(incident.id)) % 900 + 100}"
        url = f"{settings.jira_base_url.rstrip('/')}/browse/{key}" if settings.jira_base_url else f"https://demo.atlassian.net/browse/{key}"
        return ToolResult(ok=True, action="create_jira_issue", message=f"Mock Jira issue created: {key}", external_id=key, url=url)

    auth = base64.b64encode(f"{settings.jira_email}:{settings.jira_api_token}".encode()).decode()
    fields = {
        "project": {"key": settings.jira_project_key},
        "summary": f"[{incident.severity}] {incident.title}",
        "description": _jira_description(incident),
        "issuetype": {"name": "Task"},
        "labels": ["incidentforge", "incident", incident.severity.lower(), *incident.affected_services],
        "priority": {"name": PRIORITY_MAP[incident.severity]},
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.jira_base_url.rstrip('/')}/rest/api/2/issue",
                headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
                json={"fields": fields},
            )
            response.raise_for_status()
        data = response.json()
        key = data["key"]
        return ToolResult(ok=True, action="create_jira_issue", message=f"Created Jira issue {key}", external_id=key, url=f"{settings.jira_base_url.rstrip('/')}/browse/{key}", raw=data)
    except Exception as exc:
        return ToolResult(ok=False, action="create_jira_issue", message=f"Jira issue creation failed: {exc}")


async def add_jira_comment(issue_key: str, comment: str, settings: Settings | None = None) -> ToolResult:
    settings = settings or get_settings()
    if settings.demo_mode or not settings.jira_configured:
        return ToolResult(ok=True, action="add_jira_comment", message=f"Mock Jira comment added to {issue_key}")
    auth = base64.b64encode(f"{settings.jira_email}:{settings.jira_api_token}".encode()).decode()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.jira_base_url.rstrip('/')}/rest/api/2/issue/{issue_key}/comment",
                headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
                json={"body": comment},
            )
            response.raise_for_status()
        return ToolResult(ok=True, action="add_jira_comment", message=f"Added Jira comment to {issue_key}")
    except Exception as exc:
        return ToolResult(ok=False, action="add_jira_comment", message=f"Jira comment failed: {exc}")


def _jira_description(incident: Incident) -> str:
    return f"""h2. Incident Summary
Severity: {incident.severity}
Affected Services: {", ".join(incident.affected_services) or "Unknown"}
Symptoms: {", ".join(incident.symptoms) or "Unknown"}

h2. Initial Report
{incident.original_message}

h2. Links
Slack Channel: TBD
Confluence Page: TBD
PagerDuty Alert: TBD

h2. Incident Timeline
Timeline will be updated by IncidentForge.
"""
