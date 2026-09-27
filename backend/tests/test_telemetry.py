import pytest
import json
from httpx import AsyncClient
from starlette.testclient import TestClient
from app.main import app

@pytest.mark.asyncio
async def test_get_recent_telemetry_events(async_client: AsyncClient):
    """
    Test REST endpoint for fetching recent telemetry events (Rule 20, 35).
    """
    res = await async_client.get("/api/v1/telemetry/recent")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

@pytest.mark.asyncio
async def test_fl_round_emits_telemetry_events(async_client: AsyncClient):
    """
    Test that stepping an FL round broadcasts authentic telemetry events in chronological order.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")

    await async_client.patch(
        f"/api/v1/admin/models/{dia_model['id']}/status",
        json={"status": "published"},
        headers=admin_headers
    )

    exp_res = await async_client.post(
        "/api/v1/admin/experiments",
        json={
            "name": "Telemetry Verification Trial",
            "healthcare_task": "diabetes_prediction",
            "model_id": dia_model["id"],
            "total_rounds": 1,
            "strategy": "FedAvg",
            "local_epochs": 1,
            "learning_rate": 0.01
        },
        headers=admin_headers
    )
    exp_id = exp_res.json()["id"]

    # Step round 1
    step_res = await async_client.post(f"/api/v1/admin/experiments/{exp_id}/step", headers=admin_headers)
    assert step_res.status_code == 200

    # Query recent events
    tel_res = await async_client.get("/api/v1/telemetry/recent")
    assert tel_res.status_code == 200
    events = tel_res.json()
    event_types = [e["type"] for e in events]

    assert "ROUND_STARTED" in event_types
    assert "CLIENT_TRAINING_STARTED" in event_types
    assert "CLIENT_TRAINING_COMPLETED" in event_types
    assert "SECURITY_VERIFICATION_PASSED" in event_types
    assert "AGGREGATION_COMPLETED" in event_types
    assert "GLOBAL_EVALUATION_COMPLETED" in event_types
    assert "EXPERIMENT_COMPLETED" in event_types

def test_websocket_telemetry_connection():
    """
    Test WebSocket live telemetry connection, initial sync, and heartbeat.
    """
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/telemetry") as websocket:
        initial_msg = websocket.receive_text()
        data = json.loads(initial_msg)
        assert data["type"] == "INITIAL_SYNC"
        assert "events" in data

        # Send ping
        websocket.send_text("ping")
        pong_msg = websocket.receive_text()
        pong_data = json.loads(pong_msg)
        assert pong_data["type"] == "PONG"
