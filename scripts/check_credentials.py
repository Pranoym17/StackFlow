from __future__ import annotations

import sys
import argparse
from dataclasses import dataclass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings


@dataclass(frozen=True)
class IntegrationCheck:
    name: str
    ready: bool
    required_keys: tuple[str, ...]
    note: str
    warnings: tuple[str, ...] = ()


def main() -> None:
    parser = argparse.ArgumentParser(description="Check IncidentForge environment readiness.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if live-mode required credentials are missing.")
    args = parser.parse_args()

    get_settings.cache_clear()
    settings = get_settings()
    checks = [
        IntegrationCheck(
            "OpenAI",
            bool(settings.openai_api_key),
            ("OPENAI_API_KEY",),
            "Required for live AI planner/status/postmortem. Fallback parser works without it.",
        ),
        IntegrationCheck(
            "Slack",
            settings.slack_configured and bool(settings.slack_signing_secret),
            ("SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"),
            "Required for slash commands, buttons, and Slack posting.",
        ),
        IntegrationCheck(
            "Jira",
            settings.jira_configured and bool(settings.jira_project_key),
            ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"),
            "Jira is the source of truth. Real execution needs these.",
            _url_warnings("JIRA_BASE_URL", settings.jira_base_url, settings),
        ),
        IntegrationCheck(
            "Confluence",
            settings.confluence_configured and bool(settings.confluence_space_id),
            (
                "CONFLUENCE_BASE_URL",
                "CONFLUENCE_EMAIL",
                "CONFLUENCE_API_TOKEN",
                "CONFLUENCE_SPACE_ID",
            ),
            "Needed for live runbook and postmortem pages.",
            _url_warnings("CONFLUENCE_BASE_URL", settings.confluence_base_url, settings),
        ),
        IntegrationCheck(
            "PagerDuty",
            settings.pagerduty_configured,
            ("PAGERDUTY_ROUTING_KEY",),
            "Needed for real alert triggering. Mock mode works without it.",
        ),
        IntegrationCheck(
            "Upstash Redis",
            settings.redis_configured,
            ("UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"),
            "Needed for durable state. In-memory state works locally without it.",
            _url_warnings("UPSTASH_REDIS_REST_URL", settings.upstash_redis_rest_url, settings),
        ),
    ]
    print("IncidentForge credential readiness")
    print(f"DEMO_MODE={settings.demo_mode}")
    print(f"APP_BASE_URL={settings.app_base_url}")
    for warning in _url_warnings("APP_BASE_URL", settings.app_base_url, settings):
        print(f"WARNING: {warning}")
    if settings.slack_configured and settings.app_base_url.startswith("http://localhost"):
        print("WARNING: Slack needs a public HTTPS APP_BASE_URL for real slash commands.")
    print()
    for check in checks:
        status = "READY" if check.ready else "MISSING"
        print(f"[{status}] {check.name}")
        print(f"  Keys: {', '.join(check.required_keys)}")
        print(f"  {check.note}")
        for warning in check.warnings:
            print(f"  WARNING: {warning}")
    print()
    if settings.demo_mode:
        print("Tip: set DEMO_MODE=false after real Jira/Slack credentials are verified.")
    elif not settings.live_mode_ready:
        print("Live mode is not ready: OpenAI, Slack, and Jira credentials are required.")
        if args.strict:
            raise SystemExit(1)


def _url_warnings(name: str, value: str, settings) -> tuple[str, ...]:
    if not value:
        return ()
    if not settings.has_url_scheme(value):
        return (f"{name} should include http:// or https://.",)
    return ()


if __name__ == "__main__":
    main()
