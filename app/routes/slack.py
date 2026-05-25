from __future__ import annotations

import json

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from app.ai.planner import create_action_plan
from app.ai.status import summarize_status
from app.routes.incidents import create_postmortem
from app.services.incident_service import incident_service
from app.services.orchestrator import orchestrator

router = APIRouter(prefix="/slack", tags=["slack"])


@router.post("/commands")
async def slack_command(
    text: str = Form(""),
    user_id: str = Form("demo-user"),
    channel_id: str = Form("demo-channel"),
) -> JSONResponse:
    command_text = text.strip()
    if command_text == "status":
        return JSONResponse({"response_type": "ephemeral", "text": await _active_status(channel_id, user_id)})
    if command_text == "timeline":
        return JSONResponse({"response_type": "ephemeral", "text": await _active_timeline(channel_id, user_id)})
    if command_text.startswith("resolve"):
        summary = command_text.replace("resolve", "", 1).strip() or "Resolved"
        return JSONResponse({"response_type": "in_channel", "text": await _resolve_active(channel_id, user_id, summary)})
    if command_text == "postmortem":
        incident_id = await incident_service.get_active_incident_id(channel_id, user_id)
        if not incident_id:
            return JSONResponse({"response_type": "ephemeral", "text": "No active incident found."})
        result = await create_postmortem(incident_id)
        return JSONResponse({"response_type": "ephemeral", "text": result["postmortem"]})

    plan = await create_action_plan(command_text, user_id, channel_id)
    await incident_service.save_plan(plan)
    return JSONResponse(
        {
            "response_type": "ephemeral",
            "text": _format_plan(plan),
            "attachments": [
                {
                    "text": "Confirm workflow?",
                    "callback_id": "incidentforge_plan",
                    "actions": [
                        {"name": "confirm", "text": "Confirm", "type": "button", "value": plan.id},
                        {"name": "cancel", "text": "Cancel", "type": "button", "value": plan.id},
                    ],
                }
            ],
        }
    )


@router.post("/actions")
async def slack_actions(payload: str = Form(...)) -> JSONResponse:
    data = json.loads(payload)
    action = data.get("actions", [{}])[0]
    plan_id = action.get("value")
    if action.get("name") == "cancel":
        return JSONResponse({"text": "Incident workflow cancelled."})
    plan = await incident_service.get_plan(plan_id)
    if not plan:
        return JSONResponse({"text": "Plan expired or not found."})
    response = await orchestrator.execute(plan, confirmed=True)
    return JSONResponse({"text": _format_execution(response.results, response.links.dashboard_url)})


async def _active_status(channel_id: str, user_id: str) -> str:
    incident_id = await incident_service.get_active_incident_id(channel_id, user_id)
    if not incident_id:
        return "No active incident found."
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        return "No active incident found."
    timeline = await incident_service.get_timeline(incident_id)
    links = await incident_service.get_links(incident_id)
    return await summarize_status(incident, timeline, links)


async def _active_timeline(channel_id: str, user_id: str) -> str:
    incident_id = await incident_service.get_active_incident_id(channel_id, user_id)
    if not incident_id:
        return "No active incident found."
    timeline = await incident_service.get_timeline(incident_id)
    return "\n".join(f"{event.timestamp.isoformat()} - {event.summary}" for event in timeline) or "No timeline events yet."


async def _resolve_active(channel_id: str, user_id: str, summary: str) -> str:
    incident_id = await incident_service.get_active_incident_id(channel_id, user_id)
    if not incident_id:
        return "No active incident found."
    result = await create_postmortem(incident_id, summary)
    incident = await incident_service.get_incident(incident_id)
    if incident:
        incident.status = "resolved"
        await incident_service.save_incident(incident)
        await incident_service.append_event(incident_id, "Incident Commander", "incident_resolved", f"Resolved incident: {summary}")
    return "Incident resolved and postmortem draft generated.\n\n" + result["postmortem"]


def _format_plan(plan) -> str:
    incident = plan.incident
    return "\n".join(
        [
            "IncidentForge detected:",
            f"Severity: {incident.severity}",
            f"Service: {', '.join(incident.affected_services) or 'unknown'}",
            f"Symptoms: {', '.join(incident.symptoms) or 'unknown'}",
            f"Team: {', '.join(incident.teams_to_notify) or 'unknown'}",
            f"People to page: {', '.join(incident.people_to_page) or 'none'}",
            "",
            "Planned actions:",
            *[f"- {action}" for action in plan.actions],
        ]
    )


def _format_execution(results, dashboard_url: str | None) -> str:
    lines = ["Incident created."]
    lines.extend(f"- {result.message}" for result in results)
    if dashboard_url:
        lines.append(f"Dashboard: {dashboard_url}")
    return "\n".join(lines)
