from __future__ import annotations

from slack_sdk.web.async_client import AsyncWebClient

from app.config import Settings, get_settings
from app.models import Incident, ToolResult


async def create_slack_incident_channel(incident: Incident, settings: Settings | None = None) -> ToolResult:
    settings = settings or get_settings()
    channel_name = _channel_name(incident)
    if settings.demo_mode or not settings.slack_configured:
        return ToolResult(
            ok=True,
            action="create_slack_channel",
            message=f"Mock Slack incident channel created: #{channel_name}",
            external_id=f"CDEMO{incident.id[-6:]}",
            url=f"https://slack.com/app_redirect?channel={channel_name}",
        )
    try:
        client = AsyncWebClient(token=settings.slack_bot_token)
        response = await client.conversations_create(name=channel_name)
        channel_id = response["channel"]["id"]
        await client.chat_postMessage(channel=channel_id, text=f"Incident started: {incident.title}")
        return ToolResult(ok=True, action="create_slack_channel", message=f"Created Slack channel #{channel_name}", external_id=channel_id, url=f"https://slack.com/app_redirect?channel={channel_id}", raw=dict(response))
    except Exception as exc:
        return ToolResult(ok=False, action="create_slack_channel", message=f"Slack channel creation failed: {exc}")


async def post_slack_message(channel_id: str, text: str, settings: Settings | None = None) -> ToolResult:
    settings = settings or get_settings()
    if settings.demo_mode or not settings.slack_configured:
        return ToolResult(ok=True, action="post_slack_message", message=f"Mock Slack message posted to {channel_id}", raw={"text": text})
    try:
        client = AsyncWebClient(token=settings.slack_bot_token)
        response = await client.chat_postMessage(channel=channel_id, text=text)
        return ToolResult(ok=True, action="post_slack_message", message=f"Posted Slack message to {channel_id}", raw=dict(response))
    except Exception as exc:
        return ToolResult(ok=False, action="post_slack_message", message=f"Slack message failed: {exc}")


def _channel_name(incident: Incident) -> str:
    service = incident.affected_services[0] if incident.affected_services else "incident"
    return f"incident-{service}-{incident.created_at:%Y%m%d}".lower().replace("_", "-")
