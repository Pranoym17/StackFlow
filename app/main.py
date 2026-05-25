from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import dashboard, incidents, slack
from app.services.reminders import reminder_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    reminder_service.start()
    yield
    reminder_service.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="IncidentForge", version="0.1.0", lifespan=lifespan)
    app.include_router(incidents.router)
    app.include_router(slack.router)
    app.include_router(dashboard.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "incidentforge"}

    return app


app = create_app()
