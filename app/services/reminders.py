from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.models import ToolResult


class ReminderService:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def schedule_reminder(self, incident_id: str, minutes: int | None) -> ToolResult:
        minutes = minutes or 20
        run_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        self.scheduler.add_job(
            self._noop_reminder,
            "date",
            run_date=run_at,
            args=[incident_id],
            id=f"reminder-{incident_id}-{int(run_at.timestamp())}",
            replace_existing=True,
        )
        return ToolResult(
            ok=True,
            action="schedule_reminder",
            message=f"Scheduled {minutes}-minute update reminder for {incident_id}",
            external_id=run_at.isoformat(),
        )

    async def _noop_reminder(self, incident_id: str) -> None:
        return None


reminder_service = ReminderService()
