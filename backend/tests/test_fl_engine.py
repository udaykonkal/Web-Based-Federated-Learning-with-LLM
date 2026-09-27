import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_fl_experiment_lifecycle_and_fedavg(async_client: AsyncClient):
    """
    Test Phase 6: Federated Learning Engine & FedAvg Aggregation (Rules 4, 19, 25, 26, 27).
      1. Admin creates FL experiment for Diabetes Prediction.
      2. Step Round 1: Local training on all 3 clients -> FedAvg weighted aggregation -> Benchmark eval.
      3. Verify total samples aggregated = 768 (345 + 268 + 155).
      4. Step Round 2 & 3: Multi-round convergence curve tracked.
      5. Experiment transitions to 'completed'.
    """
    # 1. Admin login
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # Ensure Diabetes model is published
    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")

    await async_client.patch(
        f"/api/v1/admin/models/{dia_model['id']}/status",
        json={"status": "published"},
        headers=admin_headers
    )

    # 2. Create Experiment
    exp_res = await async_client.post(
        "/api/v1/admin/experiments",
        json={
            "name": "Benchmark Diabetes FedAvg Experiment",
            "healthcare_task": "diabetes_prediction",
            "model_id": dia_model["id"],
            "total_rounds": 3,
            "strategy": "FedAvg",
            "local_epochs": 2,
            "learning_rate": 0.01,
            "batch_size": 16
        },
        headers=admin_headers
    )
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    exp_id = exp_data["id"]
    assert exp_data["status"] == "created"
    assert exp_data["current_round"] == 0
    assert exp_data["total_rounds"] == 3

    # 3. Step Round 1
    r1_res = await async_client.post(
        f"/api/v1/admin/experiments/{exp_id}/step",
        headers=admin_headers
    )
    assert r1_res.status_code == 200
    r1 = r1_res.json()
    assert r1["round_number"] == 1
    assert r1["status"] == "completed"
    assert r1["global_accuracy"] > 0.4
    assert r1["global_loss"] > 0.0
    assert len(r1["participating_clients"]) == 3
    assert r1["aggregation_metrics"]["total_samples"] == 768
    assert "client_1" in r1["aggregation_metrics"]["client_weights"]
    assert "client_2" in r1["aggregation_metrics"]["client_weights"]
    assert "client_3" in r1["aggregation_metrics"]["client_weights"]

    # 4. Step Round 2
    r2_res = await async_client.post(
        f"/api/v1/admin/experiments/{exp_id}/step",
        headers=admin_headers
    )
    assert r2_res.status_code == 200
    r2 = r2_res.json()
    assert r2["round_number"] == 2
    assert r2["status"] == "completed"

    # 5. Step Round 3 (Final Round)
    r3_res = await async_client.post(
        f"/api/v1/admin/experiments/{exp_id}/step",
        headers=admin_headers
    )
    assert r3_res.status_code == 200
    r3 = r3_res.json()
    assert r3["round_number"] == 3
    assert r3["status"] == "completed"

    # Verify Experiment is now completed
    exp_final = await async_client.get(f"/api/v1/admin/experiments/{exp_id}", headers=admin_headers)
    assert exp_final.status_code == 200
    exp_final_data = exp_final.json()
    assert exp_final_data["status"] == "completed"
    assert exp_final_data["current_round"] == 3
    assert len(exp_final_data["rounds"]) == 3
    assert exp_final_data["final_accuracy"] is not None

@pytest.mark.asyncio
async def test_heart_disease_fl_experiment(async_client: AsyncClient):
    """
    Test multi-round FedAvg execution on Heart Disease prediction task.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    heart_model = next(m for m in models_res.json() if m["healthcare_task"] == "heart_disease_prediction")

    await async_client.patch(
        f"/api/v1/admin/models/{heart_model['id']}/status",
        json={"status": "published"},
        headers=admin_headers
    )

    exp_res = await async_client.post(
        "/api/v1/admin/experiments",
        json={
            "name": "Cardiology FedAvg Trial",
            "healthcare_task": "heart_disease_prediction",
            "model_id": heart_model["id"],
            "total_rounds": 2,
            "strategy": "FedAvg",
            "local_epochs": 2,
            "learning_rate": 0.005
        },
        headers=admin_headers
    )
    assert exp_res.status_code == 200
    exp_id = exp_res.json()["id"]

    # Run full experiment sequentially
    run_res = await async_client.post(
        f"/api/v1/admin/experiments/{exp_id}/run",
        headers=admin_headers
    )
    assert run_res.status_code == 200
    rounds = run_res.json()
    assert len(rounds) == 2
    assert rounds[0]["round_number"] == 1
    assert rounds[1]["round_number"] == 2
    assert rounds[0]["aggregation_metrics"]["total_samples"] == 303

@pytest.mark.asyncio
async def test_client_forbidden_from_admin_experiments(async_client: AsyncClient):
    """
    Test that clinical clients cannot access Admin experiment endpoints (Rule 18).
    """
    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    # Client attempting to list experiments
    res = await async_client.get("/api/v1/admin/experiments", headers=c1_headers)
    assert res.status_code == 403
    assert "Administrative privileges required" in res.json()["detail"]

    # Client attempting to trigger round step
    step_res = await async_client.post("/api/v1/admin/experiments/1/step", headers=c1_headers)
    assert step_res.status_code == 403
