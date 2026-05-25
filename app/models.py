from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


Severity = Literal["P0", "P1", "P2", "P3"]
IncidentStatus = Literal["planned", "active", "resolved"]
ActionName = Literal[
    "create_jira_issue",
    "create_slack_channel",
    "create_confluence_page",
    "trigger_pagerduty",
    "schedule_reminder",
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_incident_id() -> str:
    return f"INC-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}"


class Incident(BaseModel):
    id: str = Field(default_factory=new_incident_id)
    title: str
    severity: Severity
    affected_services: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    teams_to_notify: list[str] = Field(default_factory=list)
    people_to_page: list[str] = Field(default_factory=list)
    status: IncidentStatus = "planned"
    original_message: str
    created_by: str
    slack_channel_id: str | None = None
    jira_issue_key: str | None = None
    confluence_page_id: str | None = None
    pagerduty_dedup_key: str | None = None
    reminder_minutes: int | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ActionPlan(BaseModel):
    id: str = Field(default_factory=lambda: f"plan_{uuid4().hex}")
    incident: Incident
    actions: list[ActionName]
    confirmation_required: bool = True
    rationale: str
    missing_info: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    timestamp: datetime = Field(default_factory=utcnow)
    incident_id: str
    actor: str
    type: str
    summary: str
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    ok: bool
    action: str
    message: str
    external_id: str | None = None
    url: str | None = None
    raw: dict[str, Any] | None = None


class IncidentLinks(BaseModel):
    jira_url: str | None = None
    slack_channel_url: str | None = None
    confluence_url: str | None = None
    pagerduty_url: str | None = None
    dashboard_url: str | None = None


class ExecuteResponse(BaseModel):
    incident: Incident
    links: IncidentLinks
    results: list[ToolResult]


class ResolveRequest(BaseModel):
    summary: str


class PlanRequest(BaseModel):
    message: str
    created_by: str = "demo-user"
    slack_channel_id: str | None = None
