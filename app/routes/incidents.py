from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.planner import create_action_plan
from app.ai.postmortem import generate_postmortem
from app.ai.status import summarize_status
from app.models import ActionPlan, ExecuteResponse, PlanRequest, ResolveRequest, ToolResult, utcnow
from app.services.incident_service import incident_service
from app.services.orchestrator import orchestrator
from app.tools.confluence import update_confluence_page
from app.tools.jira import add_jira_comment
from app.tools.slack_client import post_slack_message

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


class ExecuteRequest(BaseModel):
    plan_id: str | None = None
    confirmed: bool = True


@router.post("/plan", response_model=ActionPlan)
async def plan_incident(request: PlanRequest) -> ActionPlan:
    plan = await create_action_plan(request.message, request.created_by, request.slack_channel_id)
    await incident_service.save_plan(plan)
    return plan


@router.post("/{incident_id}/execute", response_model=ExecuteResponse)
async def execute_incident(incident_id: str, request: ExecuteRequest) -> ExecuteResponse:
    plan = await _load_plan(incident_id, request.plan_id)
    return await orchestrator.execute(plan, confirmed=request.confirmed)


@router.get("/{incident_id}")
async def get_incident(incident_id: str) -> dict:
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    links = await incident_service.get_links(incident_id)
    return {"incident": incident, "links": links}


@router.get("/{incident_id}/timeline")
async def get_timeline(incident_id: str) -> list:
    return await incident_service.get_timeline(incident_id)


@router.get("/{incident_id}/status")
async def get_status(incident_id: str) -> dict[str, str]:
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    timeline = await incident_service.get_timeline(incident_id)
    links = await incident_service.get_links(incident_id)
    return {"status": await summarize_status(incident, timeline, links)}


@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str, request: ResolveRequest) -> dict:
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = "resolved"
    incident.updated_at = utcnow()
    await incident_service.save_incident(incident)
    await incident_service.append_event(
        incident_id,
        "Incident Commander",
        "incident_resolved",
        f"Resolved incident: {request.summary}",
        metadata={"summary": request.summary},
    )
    if incident.jira_issue_key:
        await add_jira_comment(incident.jira_issue_key, f"Incident resolved: {request.summary}")
    if incident.slack_channel_id:
        await post_slack_message(incident.slack_channel_id, f"Incident resolved: {request.summary}")
    return await create_postmortem(incident_id, request.summary)


@router.post("/{incident_id}/postmortem")
async def create_postmortem(incident_id: str, resolution_summary: str | None = None) -> dict[str, str]:
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    timeline = await incident_service.get_timeline(incident_id)
    links = await incident_service.get_links(incident_id)
    markdown = await generate_postmortem(incident, timeline, links, resolution_summary)
    result: ToolResult | None = None
    if incident.confluence_page_id:
        result = await update_confluence_page(incident.confluence_page_id, markdown)
    await incident_service.append_event(
        incident_id,
        "IncidentForge",
        "postmortem_generated",
        "Generated postmortem draft",
        metadata={"confluence_update": result.model_dump(mode="json") if result else None},
    )
    return {"postmortem": markdown}


async def _load_plan(incident_id: str, plan_id: str | None) -> ActionPlan:
    if plan_id:
        plan = await incident_service.get_plan(plan_id)
        if plan:
            return plan
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident plan not found")
    return ActionPlan(
        incident=incident,
        actions=[
            "create_jira_issue",
            "create_slack_channel",
            "create_confluence_page",
            "trigger_pagerduty",
            "schedule_reminder",
        ],
        confirmation_required=True,
        rationale="Default execution plan reconstructed for incident.",
    )
