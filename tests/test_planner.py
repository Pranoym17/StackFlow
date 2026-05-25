from app.ai.planner import fallback_plan


def test_fallback_plan_extracts_demo_command() -> None:
    plan = fallback_plan(
        "P1 down. Checkout service returning 500s. Notify backend, create a critical Jira ticket, open an incident channel, page Sarah, and remind us in 20 minutes.",
        created_by="U123",
        slack_channel_id="C123",
    )

    assert plan.incident.severity == "P1"
    assert plan.incident.affected_services == ["checkout"]
    assert "500 errors" in plan.incident.symptoms
    assert plan.incident.teams_to_notify == ["backend"]
    assert plan.incident.people_to_page == ["Sarah"]
    assert plan.incident.reminder_minutes == 20
    assert plan.confirmation_required is True
    assert plan.actions == [
        "create_jira_issue",
        "create_slack_channel",
        "create_confluence_page",
        "trigger_pagerduty",
        "schedule_reminder",
    ]
