from __future__ import annotations

import argparse
import sys

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test a hosted IncidentForge backend.")
    parser.add_argument("base_url", help="Example: https://incidentforge.onrender.com")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    with httpx.Client(timeout=20) as client:
        health = client.get(f"{base_url}/health")
        health.raise_for_status()
        plan = client.post(
            f"{base_url}/api/incidents/plan",
            json={
                "message": "P1 down. Checkout service returning 500s. Notify backend, page Sarah, and remind us in 20 minutes.",
                "created_by": "smoke-test",
                "slack_channel_id": "smoke-test-channel",
            },
        )
        plan.raise_for_status()
        plan_body = plan.json()
        incident_id = plan_body["incident"]["id"]
        execute = client.post(
            f"{base_url}/api/incidents/{incident_id}/execute",
            json={"plan_id": plan_body["id"], "confirmed": True},
        )
        execute.raise_for_status()
        dashboard = client.get(f"{base_url}/dashboard/incidents/{incident_id}")
        dashboard.raise_for_status()
    print("Smoke test passed")
    print(f"Incident: {incident_id}")
    print(f"Dashboard: {base_url}/dashboard/incidents/{incident_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
