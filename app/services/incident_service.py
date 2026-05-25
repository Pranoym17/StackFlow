from __future__ import annotations

from app.models import ActionPlan, Incident, IncidentLinks, TimelineEvent
from app.state.redis_store import IncidentStore, store


class IncidentService:
    def __init__(self, incident_store: IncidentStore | None = None) -> None:
        self.store = incident_store or store

    async def save_plan(self, plan: ActionPlan) -> None:
        await self.store.save_incident(plan.incident)
        await self.store.save_plan(plan)
        await self.append_event(
            plan.incident.id,
            "IncidentForge",
            "plan_created",
            f"Created action plan with {len(plan.actions)} actions",
            metadata={"actions": plan.actions, "plan_id": plan.id},
        )

    async def get_plan(self, plan_id: str) -> ActionPlan | None:
        return await self.store.get_plan(plan_id)

    async def save_incident(self, incident: Incident) -> None:
        await self.store.save_incident(incident)

    async def get_incident(self, incident_id: str) -> Incident | None:
        return await self.store.get_incident(incident_id)

    async def append_event(
        self,
        incident_id: str,
        actor: str,
        event_type: str,
        summary: str,
        url: str | None = None,
        metadata: dict | None = None,
    ) -> TimelineEvent:
        event = TimelineEvent(
            incident_id=incident_id,
            actor=actor,
            type=event_type,
            summary=summary,
            url=url,
            metadata=metadata or {},
        )
        await self.store.append_timeline(event)
        return event

    async def get_timeline(self, incident_id: str) -> list[TimelineEvent]:
        return await self.store.get_timeline(incident_id)

    async def get_links(self, incident_id: str) -> IncidentLinks:
        return await self.store.get_links(incident_id)

    async def save_links(self, incident_id: str, links: IncidentLinks) -> None:
        await self.store.save_links(incident_id, links)

    async def set_active(self, incident: Incident) -> None:
        if incident.slack_channel_id:
            await self.store.set_active_for_channel(incident.slack_channel_id, incident.id)
        await self.store.set_active_for_user(incident.created_by, incident.id)

    async def get_active_incident_id(self, channel_id: str | None, user_id: str | None) -> str | None:
        if channel_id:
            incident_id = await self.store.get_active_for_channel(channel_id)
            if incident_id:
                return incident_id
        if user_id:
            return await self.store.get_active_for_user(user_id)
        return None


incident_service = IncidentService()
