from __future__ import annotations

import httpx

from app.config import Settings, get_settings
from app.models import Incident, ToolResult


async def trigger_pagerduty(incident: Incident, settings: Settings | None = None) -> ToolResult:
    settings = settings or get_settings()
    dedup_key = f"incidentforge-{incident.id.lower()}"
    if settings.demo_mode or not settings.pagerduty_configured:
        return ToolResult(ok=True, action="trigger_pagerduty", message="Mock PagerDuty alert triggered", external_id=dedup_key, url="https://events.pagerduty.com/demo")
    payload = {
        "routing_key": settings.pagerduty_routing_key,
        "event_action": "trigger",
        "dedup_key": dedup_key,
        "payload": {
            "summary": f"{incident.severity} {incident.title}",
            "severity": "critical" if incident.severity in {"P0", "P1"} else "warning",
            "source": "IncidentForge",
            "component": incident.affected_services[0] if incident.affected_services else "unknown",
            "group": incident.teams_to_notify[0] if incident.teams_to_notify else "unknown",
            "class": "incident",
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post("https://events.pagerduty.com/v2/enqueue", json=payload)
            response.raise_for_status()
        data = response.json()
        return ToolResult(ok=True, action="trigger_pagerduty", message="Triggered PagerDuty alert", external_id=dedup_key, raw=data)
    except Exception as exc:
        return ToolResult(ok=False, action="trigger_pagerduty", message=f"PagerDuty trigger failed: {exc}")
