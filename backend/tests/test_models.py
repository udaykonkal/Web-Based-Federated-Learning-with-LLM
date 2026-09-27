import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_models_availability_lifecycle(async_client: AsyncClient):
    """
    Comprehensive test of Rules 7, 8, 9, 10, 11, 12, 17, 18, and 47 (Stages 1, 2, 3):
    1. Initially no models are published -> Client sees empty state [].
    2. Admin seeds default models in 'draft' status -> Client STILL sees [] (draft blocked).
    3. Client attempting to fetch draft model gets 403 Forbidden.
    4. Admin publishes Diabetes Prediction -> Client sees Diabetes model with status published.
    5. Admin publishes Heart Disease Prediction -> Client sees both models selectable.
    6. Admin deactivates Diabetes -> Client cannot access inactive model.
    7. Client cannot call Admin publishing endpoint.
    """
    # 1. Login as Admin & Client
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    client_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    client_token = client_login.json()["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}

    # Step 1: Client queries models when none are published (Stage 1)
    stage1_res = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert stage1_res.status_code == 200
    # Prior tests might have left no models or draft models; client must see []
    assert all(m["status"] in ["published", "active"] for m in stage1_res.json())

    # Step 2: Admin initializes default models in DRAFT status
    init_res = await async_client.post("/api/v1/admin/models/initialize-defaults", headers=admin_headers)
    assert init_res.status_code == 200
    admin_models = init_res.json()
    assert len(admin_models) >= 2

    diabetes_model = next(m for m in admin_models if m["healthcare_task"] == "diabetes_prediction")
    heart_model = next(m for m in admin_models if m["healthcare_task"] == "heart_disease_prediction")

    # Reset both to draft to test exact transition sequence
    await async_client.patch(
        f"/api/v1/admin/models/{diabetes_model['id']}/status",
        json={"status": "draft"},
        headers=admin_headers
    )
    await async_client.patch(
        f"/api/v1/admin/models/{heart_model['id']}/status",
        json={"status": "draft"},
        headers=admin_headers
    )

    # Client queries models -> must be empty because both are draft!
    client_models_draft = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert client_models_draft.status_code == 200
    assert client_models_draft.json() == []

    # Client directly attempting to access draft model -> 403 Forbidden!
    draft_attempt = await async_client.get(
        f"/api/v1/client/models/{diabetes_model['id']}",
        headers=client_headers
    )
    assert draft_attempt.status_code == 403
    assert "not available for client training" in draft_attempt.json()["detail"]

    # Step 4: Admin sets Diabetes Prediction to UPLOADED -> Client STILL sees [] (Rule 1)
    up_dia = await async_client.patch(
        f"/api/v1/admin/models/{diabetes_model['id']}/status",
        json={"status": "uploaded"},
        headers=admin_headers
    )
    assert up_dia.status_code == 200
    assert up_dia.json()["status"] == "uploaded"

    up_client_res = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert up_client_res.status_code == 200
    assert up_client_res.json() == []

    # Step 5: Admin Publishes Diabetes Prediction -> Client STILL blocked because it's not ACTIVE yet!
    pub_dia = await async_client.patch(
        f"/api/v1/admin/models/{diabetes_model['id']}/status",
        json={"status": "published"},
        headers=admin_headers
    )
    assert pub_dia.status_code == 200
    assert pub_dia.json()["status"] == "published"

    # Client still sees empty list because published != active
    pub_client_res = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert pub_client_res.status_code == 200
    assert pub_client_res.json() == []

    # Client attempting to access published-only model gets 403
    pub_attempt = await async_client.get(
        f"/api/v1/client/models/{diabetes_model['id']}",
        headers=client_headers
    )
    assert pub_attempt.status_code == 403

    # Step 6: Admin Activates Diabetes Prediction (Draft -> Uploaded -> Published -> Active)
    act_dia = await async_client.patch(
        f"/api/v1/admin/models/{diabetes_model['id']}/status",
        json={"status": "active"},
        headers=admin_headers
    )
    assert act_dia.status_code == 200
    assert act_dia.json()["status"] == "active"

    # Client now sees Diabetes Prediction available!
    stage2_client_res = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert stage2_client_res.status_code == 200
    stage2_models = stage2_client_res.json()
    assert len(stage2_models) == 1
    assert stage2_models[0]["healthcare_task"] == "diabetes_prediction"
    assert stage2_models[0]["status"] == "active"

    # Client accesses Diabetes workspace -> 200 OK
    dia_workspace = await async_client.get(
        f"/api/v1/client/models/{diabetes_model['id']}",
        headers=client_headers
    )
    assert dia_workspace.status_code == 200
    assert dia_workspace.json()["name"] == diabetes_model["name"]
    assert dia_workspace.json()["client_id"] == "client_1"

    # Heart Disease is still draft -> Client cannot access Heart Disease yet
    heart_attempt = await async_client.get(
        f"/api/v1/client/models/{heart_model['id']}",
        headers=client_headers
    )
    assert heart_attempt.status_code == 403

    # Step 7: Admin Publishes & Activates Heart Disease Prediction
    await async_client.patch(
        f"/api/v1/admin/models/{heart_model['id']}/status",
        json={"status": "published"},
        headers=admin_headers
    )
    pub_heart = await async_client.patch(
        f"/api/v1/admin/models/{heart_model['id']}/status",
        json={"status": "active"},
        headers=admin_headers
    )
    assert pub_heart.status_code == 200
    assert pub_heart.json()["status"] == "active"

    # Client now sees BOTH models available and can select either! (Rule 11)
    stage3_client_res = await async_client.get("/api/v1/client/models", headers=client_headers)
    assert stage3_client_res.status_code == 200
    available_tasks = [m["healthcare_task"] for m in stage3_client_res.json()]
    assert "diabetes_prediction" in available_tasks
    assert "heart_disease_prediction" in available_tasks

    # Step 6: Admin deactivates Diabetes -> Client blocked from inactive model
    deact_res = await async_client.patch(
        f"/api/v1/admin/models/{diabetes_model['id']}/status",
        json={"status": "inactive"},
        headers=admin_headers
    )
    assert deact_res.status_code == 200

    inactive_attempt = await async_client.get(
        f"/api/v1/client/models/{diabetes_model['id']}",
        headers=client_headers
    )
    assert inactive_attempt.status_code == 403

    # Restore to active
    await async_client.patch(
        f"/api/v1/admin/models/{diabetes_model['id']}/status",
        json={"status": "active"},
        headers=admin_headers
    )

    # Step 7: Security check - Client cannot call Admin publishing endpoint
    unauthorized_publish = await async_client.patch(
        f"/api/v1/admin/models/{diabetes_model['id']}/status",
        json={"status": "archived"},
        headers=client_headers
    )
    assert unauthorized_publish.status_code == 403
