from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from upstash_redis.asyncio import Redis

from app.config import Settings, get_settings
from app.models import ActionPlan, Incident, IncidentLinks, TimelineEvent


class IncidentStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.redis: Redis | None = None
        if self.settings.redis_configured:
            self.redis = Redis(
                url=self.settings.upstash_redis_rest_url,
                token=self.settings.upstash_redis_rest_token,
            )
        self._memory: dict[str, Any] = {}
        self._timelines: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def save_incident(self, incident: Incident) -> None:
        data = incident.model_dump(mode="json")
        if self.redis:
            await self.redis.set(f"incident:{incident.id}:meta", json.dumps(data))
        self._memory[f"incident:{incident.id}:meta"] = data

    async def get_incident(self, incident_id: str) -> Incident | None:
        key = f"incident:{incident_id}:meta"
        data = await self._get_json(key)
        return Incident.model_validate(data) if data else None

    async def save_links(self, incident_id: str, links: IncidentLinks) -> None:
        data = links.model_dump(mode="json")
        if self.redis:
            await self.redis.set(f"incident:{incident_id}:links", json.dumps(data))
        self._memory[f"incident:{incident_id}:links"] = data

    async def get_links(self, incident_id: str) -> IncidentLinks:
        data = await self._get_json(f"incident:{incident_id}:links")
        return IncidentLinks.model_validate(data) if data else IncidentLinks()

    async def save_plan(self, plan: ActionPlan) -> None:
        data = plan.model_dump(mode="json")
        if self.redis:
            await self.redis.set(f"incident:{plan.incident.id}:plan", json.dumps(data))
            await self.redis.set(f"pending_plan:{plan.id}", json.dumps(data))
        self._memory[f"incident:{plan.incident.id}:plan"] = data
        self._memory[f"pending_plan:{plan.id}"] = data

    async def get_plan(self, plan_id: str) -> ActionPlan | None:
        data = await self._get_json(f"pending_plan:{plan_id}")
        return ActionPlan.model_validate(data) if data else None

    async def append_timeline(self, event: TimelineEvent) -> None:
        data = event.model_dump(mode="json")
        if self.redis:
            await self.redis.rpush(f"incident:{event.incident_id}:timeline", json.dumps(data))
        self._timelines[event.incident_id].append(data)

    async def get_timeline(self, incident_id: str) -> list[TimelineEvent]:
        if self.redis:
            values = await self.redis.lrange(f"incident:{incident_id}:timeline", 0, -1)
            return [TimelineEvent.model_validate(json.loads(v)) for v in values]
        return [TimelineEvent.model_validate(v) for v in self._timelines[incident_id]]

    async def set_active_for_channel(self, channel_id: str, incident_id: str) -> None:
        key = f"active_incident:slack_channel:{channel_id}"
        if self.redis:
            await self.redis.set(key, incident_id)
        self._memory[key] = incident_id

    async def set_active_for_user(self, user_id: str, incident_id: str) -> None:
        key = f"active_incident:user:{user_id}"
        if self.redis:
            await self.redis.set(key, incident_id)
        self._memory[key] = incident_id

    async def get_active_for_channel(self, channel_id: str) -> str | None:
        return await self._get_string(f"active_incident:slack_channel:{channel_id}")

    async def get_active_for_user(self, user_id: str) -> str | None:
        return await self._get_string(f"active_incident:user:{user_id}")

    async def _get_json(self, key: str) -> dict[str, Any] | None:
        value: Any = None
        if self.redis:
            value = await self.redis.get(key)
        if value is None:
            value = self._memory.get(key)
        if value is None:
            return None
        return json.loads(value) if isinstance(value, str) else value

    async def _get_string(self, key: str) -> str | None:
        value = None
        if self.redis:
            value = await self.redis.get(key)
        return value or self._memory.get(key)


store = IncidentStore()
