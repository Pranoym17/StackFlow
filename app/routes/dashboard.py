from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.incident_service import incident_service

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_index() -> HTMLResponse:
    html = "<html><body><h1>IncidentForge</h1><p>Open /dashboard/incidents/{incident_id}</p></body></html>"
    return HTMLResponse(html)


@router.get("/dashboard/incidents/{incident_id}", response_class=HTMLResponse)
async def incident_dashboard(request: Request, incident_id: str) -> HTMLResponse:
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    timeline = await incident_service.get_timeline(incident_id)
    links = await incident_service.get_links(incident_id)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "incident": incident, "timeline": timeline, "links": links},
    )
