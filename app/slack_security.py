from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import Header, HTTPException, Request

from app.config import get_settings


async def verify_slack_request(
    request: Request,
    x_slack_request_timestamp: str | None = Header(default=None),
    x_slack_signature: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    if settings.demo_mode or not settings.slack_signing_secret:
        return
    if not x_slack_request_timestamp or not x_slack_signature:
        raise HTTPException(status_code=401, detail="Missing Slack signature headers")
    try:
        timestamp = int(x_slack_request_timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Slack timestamp") from exc
    if abs(time.time() - timestamp) > 60 * 5:
        raise HTTPException(status_code=401, detail="Stale Slack request")
    body = await request.body()
    base = f"v0:{timestamp}:{body.decode()}".encode()
    digest = hmac.new(settings.slack_signing_secret.encode(), base, hashlib.sha256).hexdigest()
    expected = f"v0={digest}"
    if not hmac.compare_digest(expected, x_slack_signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")
