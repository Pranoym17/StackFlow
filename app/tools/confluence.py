from __future__ import annotations

import base64

import httpx

from app.config import Settings, get_settings
from app.models import Incident, ToolResult


async def create_confluence_page(incident: Incident, settings: Settings | None = None) -> ToolResult:
    settings = settings or get_settings()
    title = f"Incident Runbook: {incident.severity} {incident.title}"
    if settings.demo_mode or not settings.confluence_configured:
        page_id = f"mock-conf-{incident.id[-6:]}"
        return ToolResult(ok=True, action="create_confluence_page", message=f"Mock Confluence page created: {title}", external_id=page_id, url=f"https://demo.atlassian.net/wiki/spaces/OPS/pages/{page_id}")
    auth = base64.b64encode(f"{settings.confluence_email}:{settings.confluence_api_token}".encode()).decode()
    payload = {
        "type": "page",
        "title": title,
        "space": {"id": settings.confluence_space_id},
        "body": {"storage": {"value": _runbook_body(incident), "representation": "storage"}},
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.confluence_base_url.rstrip('/')}/wiki/rest/api/content",
                headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        url = f"{settings.confluence_base_url.rstrip('/')}/wiki{data.get('_links', {}).get('webui', '')}"
        return ToolResult(ok=True, action="create_confluence_page", message=f"Created Confluence page {title}", external_id=data["id"], url=url, raw=data)
    except Exception as exc:
        return ToolResult(ok=False, action="create_confluence_page", message=f"Confluence page creation failed: {exc}")


async def update_confluence_page(page_id: str, body: str, settings: Settings | None = None) -> ToolResult:
    settings = settings or get_settings()
    if settings.demo_mode or not settings.confluence_configured:
        return ToolResult(ok=True, action="update_confluence_page", message=f"Mock Confluence page updated: {page_id}", raw={"body": body})
    return ToolResult(ok=False, action="update_confluence_page", message="Real Confluence update is not implemented in MVP.")


def _runbook_body(incident: Incident) -> str:
    return f"""<h1>Incident Runbook</h1>
<h2>Summary</h2><p>{incident.title}</p>
<h2>Severity</h2><p>{incident.severity}</p>
<h2>Affected Services</h2><p>{", ".join(incident.affected_services) or "Unknown"}</p>
<h2>Current Status</h2><p>{incident.status}</p>
<h2>Owners</h2><p>{", ".join(incident.teams_to_notify + incident.people_to_page) or "TBD"}</p>
<h2>Links</h2><p>Jira, Slack, and PagerDuty links will be added by IncidentForge.</p>
<h2>Timeline</h2><p>Timeline will be updated by IncidentForge.</p>
<h2>Known Symptoms</h2><p>{", ".join(incident.symptoms) or "Unknown"}</p>
<h2>Response Checklist</h2><ul><li>Assign incident commander</li><li>Confirm impact</li><li>Post updates</li></ul>
<h2>Notes</h2><p>{incident.original_message}</p>
"""
