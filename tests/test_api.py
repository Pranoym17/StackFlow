from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_plan_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/incidents/plan",
        json={
            "message": "P1 down. Checkout service returning 500s. Notify backend and page Sarah.",
            "created_by": "U123",
            "slack_channel_id": "C123",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["incident"]["severity"] == "P1"
    assert body["incident"]["affected_services"] == ["checkout"]
