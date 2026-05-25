from __future__ import annotations

import json
import re

from openai import AsyncOpenAI

from app.ai.prompts import PLANNER_SYSTEM_PROMPT
from app.config import Settings, get_settings
from app.models import ActionName, ActionPlan, Incident


async def create_action_plan(
    message: str,
    created_by: str,
    slack_channel_id: str | None = None,
    settings: Settings | None = None,
) -> ActionPlan:
    settings = settings or get_settings()
    if settings.openai_api_key:
        try:
            return await _openai_plan(message, created_by, slack_channel_id, settings)
        except Exception:
            pass
    return fallback_plan(message, created_by, slack_channel_id)


async def _openai_plan(
    message: str,
    created_by: str,
    slack_channel_id: str | None,
    settings: Settings,
) -> ActionPlan:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    schema = {
        "type": "object",
        "properties": {
            "incident_title": {"type": "string"},
            "severity": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
            "affected_services": {"type": "array", "items": {"type": "string"}},
            "symptoms": {"type": "array", "items": {"type": "string"}},
            "teams_to_notify": {"type": "array", "items": {"type": "string"}},
            "people_to_page": {"type": "array", "items": {"type": "string"}},
            "requested_actions": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "create_jira_issue",
                        "create_slack_channel",
                        "create_confluence_page",
                        "trigger_pagerduty",
                        "schedule_reminder",
                    ],
                },
            },
            "reminder_minutes": {"type": ["integer", "null"]},
            "confirmation_required": {"type": "boolean"},
            "missing_info": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
        "required": [
            "incident_title",
            "severity",
            "affected_services",
            "symptoms",
            "teams_to_notify",
            "people_to_page",
            "requested_actions",
            "confirmation_required",
            "missing_info",
            "rationale",
        ],
    }
    response = await client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "incident_plan",
                "schema": schema,
                "strict": False,
            }
        },
    )
    data = json.loads(response.output_text)
    incident = Incident(
        title=data["incident_title"],
        severity=data["severity"],
        affected_services=data.get("affected_services", []),
        symptoms=data.get("symptoms", []),
        teams_to_notify=data.get("teams_to_notify", []),
        people_to_page=data.get("people_to_page", []),
        original_message=message,
        created_by=created_by,
        slack_channel_id=slack_channel_id,
        reminder_minutes=data.get("reminder_minutes"),
    )
    return ActionPlan(
        incident=incident,
        actions=data["requested_actions"],
        confirmation_required=data.get("confirmation_required", True),
        rationale=data.get("rationale", "Planner generated incident response workflow."),
        missing_info=data.get("missing_info", []),
    )


def fallback_plan(message: str, created_by: str, slack_channel_id: str | None = None) -> ActionPlan:
    upper = message.upper()
    severity = next((sev for sev in ("P0", "P1", "P2", "P3") if sev in upper), "P2")
    lowered = message.lower()
    services = []
    for service in ("checkout", "payments", "api", "auth", "database", "search"):
        if service in lowered:
            services.append(service)
    teams = []
    for team in ("backend", "frontend", "sre", "devops", "support"):
        if team in lowered:
            teams.append(team)
    people = re.findall(r"\bpage\s+([A-Z][a-zA-Z]+)", message)
    symptoms = []
    if "500" in message:
        symptoms.append("500 errors")
    if "down" in lowered:
        symptoms.append("service down")
    title_service = services[0].title() if services else "Service"
    title = f"{title_service} incident"
    if "returning 500" in lowered or "500s" in lowered:
        title = f"{title_service} service returning 500s"
    actions: list[ActionName] = ["create_jira_issue", "create_slack_channel", "create_confluence_page"]
    if "page" in lowered or "pagerduty" in lowered:
        actions.append("trigger_pagerduty")
    if "remind" in lowered:
        actions.append("schedule_reminder")
    reminder_match = re.search(r"(\d+)\s*(?:minute|min)", lowered)
    incident = Incident(
        title=title,
        severity=severity,
        affected_services=services,
        symptoms=symptoms or ["reported degradation"],
        teams_to_notify=teams,
        people_to_page=people,
        original_message=message,
        created_by=created_by,
        slack_channel_id=slack_channel_id,
        reminder_minutes=int(reminder_match.group(1)) if reminder_match else None,
    )
    return ActionPlan(
        incident=incident,
        actions=actions,
        confirmation_required="trigger_pagerduty" in actions,
        rationale="Fallback parser detected incident severity, service, responders, and requested tools.",
    )
