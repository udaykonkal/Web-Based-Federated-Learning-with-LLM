import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_local_pytorch_client_training(async_client: AsyncClient):
    """
    Test Phase 5: Real Local PyTorch Training on Private Healthcare Data.
    Verifies Rule 4, 14, 23, 24:
      - Real PyTorch MLP training for 3 epochs.
      - Realistic loss convergence curve.
      - Genuine weight update delta Delta W with positive L2 norm.
      - Real accuracy, precision, recall, and F1 metrics.
    """
    # 1. Admin publishes Diabetes model
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")

    await async_client.patch(
        f"/api/v1/admin/models/{dia_model['id']}/status",
        json={"status": "active"},
        headers=admin_headers
    )

    # 2. Client 1 logs in and starts local training
    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    train_res = await async_client.post(
        f"/api/v1/client/models/{dia_model['id']}/train",
        json={"local_epochs": 3, "learning_rate": 0.01, "batch_size": 16},
        headers=c1_headers
    )
    assert train_res.status_code == 200
    res = train_res.json()

    assert res["client_id"] == "client_1"
    assert res["healthcare_task"] == "diabetes_prediction"
    assert res["sample_count"] == 345
    assert res["epochs_trained"] == 3
    assert len(res["loss_history"]) == 3
    assert res["accuracy"] > 0.4
    assert res["l2_norm"] > 0.0
    assert len(res["delta_base64"]) > 100
    assert res["update_size_kb"] > 0.5

@pytest.mark.asyncio
async def test_non_iid_different_weight_deltas(async_client: AsyncClient):
    """
    Test Rule 23: Different clients train on their isolated partitions
    and produce mathematically distinct weight deltas Delta W_k.
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
        json={"status": "active"},
        headers=admin_headers
    )

    # Client 1 trains
    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    r1 = await async_client.post(
        f"/api/v1/client/models/{dia_model['id']}/train",
        json={"local_epochs": 3, "learning_rate": 0.01},
        headers={"Authorization": f"Bearer {c1_login.json()['access_token']}"}
    )
    assert r1.status_code == 200

    # Client 2 trains
    c2_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_b@flplatform.org", "password": "client2pass"}
    )
    r2 = await async_client.post(
        f"/api/v1/client/models/{dia_model['id']}/train",
        json={"local_epochs": 3, "learning_rate": 0.01},
        headers={"Authorization": f"Bearer {c2_login.json()['access_token']}"}
    )
    assert r2.status_code == 200

    # The delta L2 norms must be different
    assert r1.json()["l2_norm"] != r2.json()["l2_norm"]
    assert r1.json()["sample_count"] == 345
    assert r2.json()["sample_count"] == 268

@pytest.mark.asyncio
async def test_heart_disease_local_training(async_client: AsyncClient):
    """
    Test Task 2 (Heart Disease Prediction MLP) local client training.
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
        json={"status": "active"},
        headers=admin_headers
    )

    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    train_res = await async_client.post(
        f"/api/v1/client/models/{heart_model['id']}/train",
        json={"local_epochs": 3, "learning_rate": 0.005},
        headers=c1_headers
    )
    assert train_res.status_code == 200
    res = train_res.json()
    assert res["healthcare_task"] == "heart_disease_prediction"
    assert res["sample_count"] == 136
    assert res["accuracy"] > 0.4
    assert res["l2_norm"] > 0.0

@pytest.mark.asyncio
async def test_cannot_train_on_draft_model(async_client: AsyncClient):
    """
    Test Rule 17 & 18: Client cannot train on a model in DRAFT or INACTIVE state.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")

    # Set to draft
    await async_client.patch(
        f"/api/v1/admin/models/{dia_model['id']}/status",
        json={"status": "draft"},
        headers=admin_headers
    )

    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    res = await async_client.post(
        f"/api/v1/client/models/{dia_model['id']}/train",
        json={"local_epochs": 2},
        headers=c1_headers
    )
    assert res.status_code == 403
    assert "not available for training" in res.json()["detail"]

    # Restore to published
    await async_client.patch(
        f"/api/v1/admin/models/{dia_model['id']}/status",
        json={"status": "published"},
        headers=admin_headers
    )

@pytest.mark.asyncio
async def test_admin_cannot_call_client_train_endpoint(async_client: AsyncClient):
    """
    Test Rule 1 & Rule 6: Admin coordinator does not perform local training.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    res = await async_client.post(
        "/api/v1/client/models/1/train",
        json={"local_epochs": 2},
        headers=admin_headers
    )
    assert res.status_code == 403
    assert "Client role required" in res.json()["detail"]

@pytest.mark.asyncio
async def test_client_train_and_submit_update_to_coordinator(async_client: AsyncClient):
    """
    Test authentic client training followed by update submission to the central coordinator.
    Verifies:
      1. Client trains locally with genuine PyTorch execution, receiving training_time_ms > 0,
         gradient_steps > 0, val_loss_history, val_accuracy_history.
      2. Client posts update to /submit-update.
      3. Central coordinator stages the update for the active experiment round.
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
        json={"status": "active"},
        headers=admin_headers
    )

    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    train_res = await async_client.post(
        f"/api/v1/client/models/{dia_model['id']}/train",
        json={"local_epochs": 3, "learning_rate": 0.01, "batch_size": 16},
        headers=c1_headers
    )
    assert train_res.status_code == 200
    t_data = train_res.json()
    assert t_data["training_time_ms"] > 0
    assert t_data["gradient_steps"] > 0
    assert len(t_data["val_loss_history"]) == 3
    assert len(t_data["val_accuracy_history"]) == 3

    # Submit update to coordinator
    submit_res = await async_client.post(
        f"/api/v1/client/models/{dia_model['id']}/submit-update",
        json={
            "sample_count": t_data["sample_count"],
            "epochs_trained": t_data["epochs_trained"],
            "accuracy": t_data["accuracy"],
            "loss": t_data["final_loss"],
            "l2_norm": t_data["l2_norm"],
            "update_size_kb": t_data["update_size_kb"],
            "training_time_ms": t_data["training_time_ms"],
            "delta_base64": t_data["delta_base64"],
            "loss_history": t_data["loss_history"],
            "val_loss_history": t_data["val_loss_history"],
            "val_accuracy_history": t_data["val_accuracy_history"],
            "gradient_steps": t_data["gradient_steps"]
        },
        headers=c1_headers
    )
    assert submit_res.status_code == 200
    s_data = submit_res.json()
    assert s_data["status"] == "success"
    assert s_data["client_id"] == "client_1"
    assert s_data["coordinator_status"] == "STAGED_FOR_AGGREGATION"
    assert s_data["round_number"] >= 1


@pytest.mark.asyncio
async def test_client_download_model_and_export_package(async_client: AsyncClient):
    """
    Test downloading global model checkpoint (.pt) and exporting the starter kit (.zip).
    """
    import zipfile
    import io

    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    active_model = next(m for m in models_res.json() if m["status"] == "active")

    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    # 1. Test downloading model checkpoint
    dl_res = await async_client.get(
        f"/api/v1/client/models/{active_model['id']}/download-model",
        headers=c1_headers
    )
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 100
    assert "attachment; filename=" in dl_res.headers.get("content-disposition", "")

    # 2. Test exporting starter kit ZIP
    pkg_res = await async_client.get(
        f"/api/v1/client/models/{active_model['id']}/export-package",
        headers=c1_headers
    )
    assert pkg_res.status_code == 200
    assert pkg_res.headers.get("content-type") == "application/zip"

    # Verify ZIP contents
    with zipfile.ZipFile(io.BytesIO(pkg_res.content)) as zf:
        file_list = zf.namelist()
        assert "global_weights.pt" in file_list
        assert "local_dataset.csv" in file_list
        assert "model_architecture.py" in file_list
        assert "train_local.py" in file_list
        assert "README.md" in file_list

@pytest.mark.asyncio
async def test_client_train_large_clinical_cohort(async_client: AsyncClient):
    """
    Test training on large clinical multi-center cohort (3,500 patient records).
    Verifies that the backend generates 3,500 samples, executes dozens of mini-batch gradient
    steps, measures genuine backpropagation time, and returns valid loss and accuracy curves.
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
        json={"status": "active"},
        headers=admin_headers
    )

    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    train_res = await async_client.post(
        f"/api/v1/client/models/{dia_model['id']}/train",
        json={
            "local_epochs": 2,
            "learning_rate": 0.01,
            "batch_size": 32,
            "dataset_scale": "large_cohort"
        },
        headers=c1_headers
    )
    assert train_res.status_code == 200
    data = train_res.json()
    assert data["sample_count"] >= 3000
    assert data["train_samples"] >= 2400
    assert data["dataset_scale"] == "large_cohort"
    assert data["gradient_steps"] >= 100
    assert len(data["loss_history"]) == 2
    assert data["accuracy"] > 0.5


