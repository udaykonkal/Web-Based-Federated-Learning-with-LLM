import pytest
import torch
import base64
from httpx import AsyncClient
from app.ml.models import deserialize_weights

@pytest.mark.asyncio
async def test_full_platform_end_to_end_pipeline(async_client: AsyncClient):
    """
    Phase 13: End-to-End Automated Integration Test Suite.
    Simulates the complete real-world healthcare FL lifecycle across Admin and Clients 1, 2, 3:
      1. Admin logs in and publishes a healthcare model.
      2. Client 1, 2, 3 log in and verify model availability.
      3. Admin creates an FL experiment with Adaptive Selection.
      4. Admin steps Round 1:
         - Clients train locally on private non-IID data.
         - Authentic weight deltas computed.
         - Mathematical security screening evaluates updates.
         - FedAvg aggregates accepted client weights.
         - Global model benchmark evaluated.
         - Telemetry events stream.
      5. Admin inspects security, communication savings, and LLM advisory.
    """
    # 1. Admin Authentication
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Publish Diabetes Model
    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    assert models_res.status_code == 200
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")

    pub_res = await async_client.patch(
        f"/api/v1/admin/models/{dia_model['id']}/status",
        json={"status": "active"},
        headers=admin_headers
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "active"

    # 3. Client 1, 2, 3 Login and Model Discovery
    client_credentials = [
        ("client_1", "hospital_a@flplatform.org", "client1pass"),
        ("client_2", "hospital_b@flplatform.org", "client2pass"),
        ("client_3", "hospital_c@flplatform.org", "client3pass"),
    ]
    client_tokens = {}
    for cid, email, pwd in client_credentials:
        c_login = await async_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": pwd}
        )
        assert c_login.status_code == 200
        client_tokens[cid] = c_login.json()["access_token"]

        c_headers = {"Authorization": f"Bearer {client_tokens[cid]}"}
        avail_res = await async_client.get("/api/v1/client/models", headers=c_headers)
        assert avail_res.status_code == 200
        assert len(avail_res.json()) >= 1
        assert any(m["id"] == dia_model["id"] for m in avail_res.json())

    # 4. Create and Step FL Experiment
    exp_res = await async_client.post(
        "/api/v1/admin/experiments",
        json={
            "name": "Final Major Project E2E Verification Trial",
            "healthcare_task": "diabetes_prediction",
            "model_id": dia_model["id"],
            "total_rounds": 2,
            "strategy": "FedAvg",
            "client_selection_mode": "adaptive",
            "local_epochs": 2,
            "learning_rate": 0.01
        },
        headers=admin_headers
    )
    assert exp_res.status_code == 200
    exp_id = exp_res.json()["id"]

    # Step Round 1
    step_res = await async_client.post(f"/api/v1/admin/experiments/{exp_id}/step", headers=admin_headers)
    assert step_res.status_code == 200
    r1_data = step_res.json()
    assert r1_data["round_number"] == 1
    assert r1_data["status"] == "completed"
    assert r1_data["global_loss"] is not None
    assert r1_data["global_accuracy"] is not None

    # Step Round 2
    step2_res = await async_client.post(f"/api/v1/admin/experiments/{exp_id}/step", headers=admin_headers)
    assert step2_res.status_code == 200
    r2_data = step2_res.json()
    assert r2_data["round_number"] == 2
    assert r2_data["status"] == "completed"

    # Verify Contributions Endpoint (Section 5)
    contrib_res = await async_client.get(f"/api/v1/admin/experiments/{exp_id}/contributions", headers=admin_headers)
    assert contrib_res.status_code == 200
    rounds_contrib = contrib_res.json()
    assert len(rounds_contrib) == 2
    assert len(rounds_contrib[0]["contributions"]) == 3
    # Verify non-faked values
    c1_c = next(c for c in rounds_contrib[0]["contributions"] if c["client_id"] == "client_1")
    assert c1_c["local_sample_count"] == 345
    assert c1_c["is_selected"] is True
    assert c1_c["is_accepted"] is True
    assert c1_c["training_status"] in ["accepted", "aggregated"]

    # 5. Verify Security Defense & Audit Log
    sec_res = await async_client.get("/api/v1/admin/security/overview", headers=admin_headers)
    assert sec_res.status_code == 200
    assert sec_res.json()["total_screened_updates"] >= 6

    # 6. Verify Communication Bandwidth Stats
    comm_res = await async_client.get("/api/v1/admin/communication/stats", headers=admin_headers)
    assert comm_res.status_code == 200
    assert comm_res.json()["average_compression_ratio"] >= 1.0

    # 7. Verify LLM AI Advisory
    llm_res = await async_client.post(
        "/api/v1/admin/llm/client-selection-advisor",
        json={"healthcare_task": "diabetes_prediction"},
        headers=admin_headers
    )
    assert llm_res.status_code == 200
    assert "selected_clients" in llm_res.json()

    # 8. Verify Comparative Analytics
    analytics_res = await async_client.get(
        "/api/v1/admin/analytics/comparison?task=diabetes_prediction",
        headers=admin_headers
    )
    assert analytics_res.status_code == 200
    assert analytics_res.json()["metrics_summary"]["final_accuracy"]["proposed"] > 0.80
