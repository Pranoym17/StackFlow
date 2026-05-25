from __future__ import annotations

from app.config import Settings, get_settings
from app.models import ActionPlan, ExecuteResponse, ToolResult, utcnow
from app.services.incident_service import IncidentService, incident_service
from app.services.reminders import reminder_service
from app.tools import confluence, jira, pagerduty, slack_client


class Orchestrator:
    def __init__(self, service: IncidentService | None = None, settings: Settings | None = None) -> None:
        self.service = service or incident_service
        self.settings = settings or get_settings()

    async def execute(self, plan: ActionPlan, confirmed: bool = False) -> ExecuteResponse:
        incident = plan.incident
        incident.status = "active"
        incident.updated_at = utcnow()
        links = await self.service.get_links(incident.id)
        links.dashboard_url = f"{self.settings.app_base_url.rstrip('/')}/dashboard/incidents/{incident.id}"
        results: list[ToolResult] = []

        if plan.confirmation_required and not confirmed:
            result = ToolResult(ok=False, action="execute_plan", message="Confirmation required before executing this plan.")
            return ExecuteResponse(incident=incident, links=links, results=[result])

        if "create_jira_issue" in plan.actions:
            result = await jira.create_jira_issue(incident, self.settings)
            results.append(result)
            await self._log_result(incident.id, result, "jira_created", "jira_failed")
            if not result.ok:
                await self.service.save_incident(incident)
                await self.service.save_links(incident.id, links)
                return ExecuteResponse(incident=incident, links=links, results=results)
            incident.jira_issue_key = result.external_id
            links.jira_url = result.url

        if "create_slack_channel" in plan.actions:
            result = await slack_client.create_slack_incident_channel(incident, self.settings)
            results.append(result)
            await self._log_result(incident.id, result, "slack_created", "slack_failed")
            if result.ok:
                incident.slack_channel_id = result.external_id or incident.slack_channel_id
                links.slack_channel_url = result.url

        if "create_confluence_page" in plan.actions:
            result = await confluence.create_confluence_page(incident, self.settings)
            results.append(result)
            await self._log_result(incident.id, result, "confluence_created", "confluence_failed")
            if result.ok:
                incident.confluence_page_id = result.external_id
                links.confluence_url = result.url

        if "trigger_pagerduty" in plan.actions:
            result = await pagerduty.trigger_pagerduty(incident, self.settings)
            results.append(result)
            await self._log_result(incident.id, result, "pagerduty_triggered", "pagerduty_failed")
            if result.ok:
                incident.pagerduty_dedup_key = result.external_id
                links.pagerduty_url = result.url

        if "schedule_reminder" in plan.actions:
            result = await reminder_service.schedule_reminder(incident.id, incident.reminder_minutes)
            results.append(result)
            await self._log_result(incident.id, result, "reminder_scheduled", "reminder_failed")

        await self.service.save_links(incident.id, links)
        await self.service.save_incident(incident)
        await self.service.set_active(incident)
        return ExecuteResponse(incident=incident, links=links, results=results)

    async def _log_result(self, incident_id: str, result: ToolResult, success_type: str, failure_type: str) -> None:
        await self.service.append_event(
            incident_id=incident_id,
            actor="IncidentForge",
            event_type=success_type if result.ok else failure_type,
            summary=result.message,
            url=result.url,
            metadata={"action": result.action, "external_id": result.external_id},
        )


orchestrator = Orchestrator()
