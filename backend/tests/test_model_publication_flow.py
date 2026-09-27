import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_draft_and_uploaded_models_invisible_to_clients(async_client: AsyncClient):
    """
    Test Section 1 & 16:
    1. Models in DRAFT status are completely invisible to clients.
    2. Models in UPLOADED status are completely invisible to clients.
    3. Direct API request for unpublished model ID is rejected with 403 Forbidden.
    """
    # Admin & Client Logins
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    client_headers = {"Authorization": f"Bearer {client_login.json()['access_token']}"}

    # Admin creates a new custom model in DRAFT status
    create_res = await async_client.post(
        "/api/v1/admin/models",
        json={
            "name": "Experimental Neural Diagnostic",
            "healthcare_task": "diabetes_prediction",
            "description": "Test model lifecycle visibility",
            "architecture": "MLP",
            "version": "v1.0",
            "status": "draft",
            "target_variable": "Outcome",
            "input_features": ["Glucose", "BMI"],
            "hyperparameters": {"lr": 0.01}
        },
        headers=admin_headers
    )
    assert create_res.status_code == 200
    model_id = create_res.json()["id"]
    assert create_res.json()["status"] == "draft"

    # Client lists models -> must NOT contain this model
    client_list1 = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert client_list1.status_code == 200
    assert not any(m["id"] == model_id for m in client_list1.json())

    # Client tries direct GET workspace for draft model -> 403 Forbidden
    direct_draft = await async_client.get(f"/api/v1/client/models/{model_id}", headers=client_headers)
    assert direct_draft.status_code == 403

    # Client tries to train on draft model -> 403 Forbidden
    train_draft = await async_client.post(
        f"/api/v1/client/models/{model_id}/train",
        json={"local_epochs": 1},
        headers=client_headers
    )
    assert train_draft.status_code == 403

    # Admin updates model to UPLOADED status
    up_res = await async_client.patch(
        f"/api/v1/admin/models/{model_id}/status",
        json={"status": "uploaded"},
        headers=admin_headers
    )
    assert up_res.status_code == 200
    assert up_res.json()["status"] == "uploaded"

    # Client lists models -> must STILL NOT contain this model
    client_list2 = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert client_list2.status_code == 200
    assert not any(m["id"] == model_id for m in client_list2.json())

    # Direct GET for uploaded model -> 403 Forbidden
    direct_uploaded = await async_client.get(f"/api/v1/client/models/{model_id}", headers=client_headers)
    assert direct_uploaded.status_code == 403


@pytest.mark.asyncio
async def test_published_model_visible_only_when_active(async_client: AsyncClient):
    """
    Test Section 1 & 16:
    1. A model in PUBLISHED status remains HIDDEN from clients until ACTIVATED.
    2. Once status becomes ACTIVE, client can discover and open the workspace.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    client_headers = {"Authorization": f"Bearer {client_login.json()['access_token']}"}

    # Fetch existing models
    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")
    model_id = dia_model["id"]

    # Step: Admin sets status to PUBLISHED
    pub_res = await async_client.patch(
        f"/api/v1/admin/models/{model_id}/status",
        json={"status": "published"},
        headers=admin_headers
    )
    assert pub_res.status_code == 200

    # Client queries available models -> Published-only model is NOT visible (Rule 1)
    c_list = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert c_list.status_code == 200
    assert not any(m["id"] == model_id for m in c_list.json())

    # Client direct workspace request for published-only model -> 403 Forbidden
    direct_pub = await async_client.get(f"/api/v1/client/models/{model_id}", headers=client_headers)
    assert direct_pub.status_code == 403

    # Step: Admin sets status to ACTIVE (both Published and Activated)
    act_res = await async_client.patch(
        f"/api/v1/admin/models/{model_id}/status",
        json={"status": "active"},
        headers=admin_headers
    )
    assert act_res.status_code == 200

    # Client now sees the model!
    c_list_active = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert c_list_active.status_code == 200
    assert any(m["id"] == model_id for m in c_list_active.json())

    # Client workspace opens successfully -> 200 OK
    workspace = await async_client.get(f"/api/v1/client/models/{model_id}", headers=client_headers)
    assert workspace.status_code == 200
    assert workspace.json()["id"] == model_id


@pytest.mark.asyncio
async def test_inactive_and_archived_models_unavailable(async_client: AsyncClient):
    """
    Test Section 1 & 16:
    INACTIVE and ARCHIVED models are rejected for client access and training.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    client_headers = {"Authorization": f"Bearer {client_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")
    model_id = dia_model["id"]

    # Deactivate model
    await async_client.patch(
        f"/api/v1/admin/models/{model_id}/status",
        json={"status": "inactive"},
        headers=admin_headers
    )

    # Client cannot see inactive model
    c_list = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert not any(m["id"] == model_id for m in c_list.json())

    # Client cannot open workspace
    w_res = await async_client.get(f"/api/v1/client/models/{model_id}", headers=client_headers)
    assert w_res.status_code == 403

    # Client cannot train
    t_res = await async_client.post(
        f"/api/v1/client/models/{model_id}/train",
        json={"local_epochs": 1},
        headers=client_headers
    )
    assert t_res.status_code == 403

    # Archive model
    await async_client.patch(
        f"/api/v1/admin/models/{model_id}/status",
        json={"status": "archived"},
        headers=admin_headers
    )
    w_arch = await async_client.get(f"/api/v1/client/models/{model_id}", headers=client_headers)
    assert w_arch.status_code == 403

    # Restore to active
    await async_client.patch(
        f"/api/v1/admin/models/{model_id}/status",
        json={"status": "active"},
        headers=admin_headers
    )


@pytest.mark.asyncio
async def test_opening_model_does_not_start_training_and_start_training_button(async_client: AsyncClient):
    """
    Test Section 2 & 3:
    1. Opening/selecting model workspace does NOT start training.
    2. Client clicking START TRAINING explicitly initiates local PyTorch training.
    3. Update submission sends genuine weight delta without raw patient records.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    client_headers = {"Authorization": f"Bearer {client_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_model = next(m for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")
    model_id = dia_model["id"]

    await async_client.patch(
        f"/api/v1/admin/models/{model_id}/status",
        json={"status": "active"},
        headers=admin_headers
    )

    # 1. Opening model workspace (GET only) — returns metadata, zero training executed
    workspace = await async_client.get(f"/api/v1/client/models/{model_id}", headers=client_headers)
    assert workspace.status_code == 200
    w_data = workspace.json()
    assert w_data["healthcare_task"] == "diabetes_prediction"
    assert w_data["client_private_data"]["sample_count"] == 345

    # 2. Client explicitly initiates START TRAINING (POST /train)
    train_res = await async_client.post(
        f"/api/v1/client/models/{model_id}/train",
        json={"local_epochs": 3, "learning_rate": 0.01, "batch_size": 16},
        headers=client_headers
    )
    assert train_res.status_code == 200
    res = train_res.json()
    assert res["epochs_trained"] == 3
    assert res["accuracy"] > 0.4
    assert res["l2_norm"] > 0.0
    assert len(res["delta_base64"]) > 50

    # 3. Client transmits weight delta to central coordinator
    submit_res = await async_client.post(
        f"/api/v1/client/models/{model_id}/submit-update",
        json={
            "sample_count": res["sample_count"],
            "epochs_trained": res["epochs_trained"],
            "accuracy": res["accuracy"],
            "l2_norm": res["l2_norm"],
            "update_size_kb": res["update_size_kb"],
            "delta_base64": res["delta_base64"],
            "loss_history": res["loss_history"]
        },
        headers=client_headers
    )
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    assert sub_data["status"] == "success"
    assert "Zero raw clinical records transmitted" in sub_data["privacy_guarantee"]
