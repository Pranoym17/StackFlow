import pytest

from app.ai.planner import fallback_plan
from app.config import Settings
from app.services.incident_service import IncidentService
from app.services.orchestrator import Orchestrator
from app.state.redis_store import IncidentStore


@pytest.mark.asyncio
async def test_orchestrator_executes_demo_workflow() -> None:
    settings = Settings(demo_mode=True, app_base_url="http://testserver")
    service = IncidentService(IncidentStore(settings))
    orchestrator = Orchestrator(service, settings)
    plan = fallback_plan(
        "P1 down. Checkout service returning 500s. Notify backend, page Sarah, and remind us in 20 minutes.",
        created_by="U123",
        slack_channel_id="C123",
    )
    await service.save_plan(plan)

    response = await orchestrator.execute(plan, confirmed=True)

    assert response.incident.status == "active"
    assert response.incident.jira_issue_key
    assert response.links.jira_url
    assert response.links.dashboard_url == f"http://testserver/dashboard/incidents/{plan.incident.id}"
    assert all(result.ok for result in response.results)
    timeline = await service.get_timeline(plan.incident.id)
    assert [event.type for event in timeline] == [
        "plan_created",
        "jira_created",
        "slack_created",
        "confluence_created",
        "pagerduty_triggered",
        "reminder_scheduled",
    ]


@pytest.mark.asyncio
async def test_orchestrator_requires_confirmation() -> None:
    settings = Settings(demo_mode=True)
    service = IncidentService(IncidentStore(settings))
    orchestrator = Orchestrator(service, settings)
    plan = fallback_plan("P1 checkout down page Sarah", created_by="U123")

    response = await orchestrator.execute(plan, confirmed=False)

    assert response.results[0].ok is False
    assert "Confirmation required" in response.results[0].message
