import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_login(async_client: AsyncClient):
    """Test that Admin can log in and receives admin role."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["client_id"] is None

@pytest.mark.asyncio
async def test_client_1_login(async_client: AsyncClient):
    """Test that Client 1 (Hospital A) can log in and receives client_1 ID."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "client"
    assert data["client_id"] == "client_1"
    assert "Hospital/Clinic A" in data["institution_name"]

@pytest.mark.asyncio
async def test_client_2_and_3_login(async_client: AsyncClient):
    """Test Client 2 and Client 3 logins and isolated identities."""
    # Client 2
    res2 = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_b@flplatform.org", "password": "client2pass"}
    )
    assert res2.status_code == 200
    assert res2.json()["client_id"] == "client_2"

    # Client 3
    res3 = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_c@flplatform.org", "password": "client3pass"}
    )
    assert res3.status_code == 200
    assert res3.json()["client_id"] == "client_3"

@pytest.mark.asyncio
async def test_invalid_credentials(async_client: AsyncClient):
    """Test that invalid password correctly yields 401 Unauthorized."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_role_enforcement_admin_endpoints(async_client: AsyncClient):
    """
    Test that a Client token CANNOT access Admin endpoints.
    Verifies Rule 41 & Rule 5: Client is forbidden from central coordinator actions.
    """
    # 1. Login as Client 1
    client_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    client_token = client_res.json()["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}

    # Attempt to call Admin Health check
    forbidden_res = await async_client.get("/api/v1/admin/health", headers=client_headers)
    assert forbidden_res.status_code == 403
    assert "Administrative privileges required" in forbidden_res.json()["detail"]

    # 2. Login as Admin and verify Admin CAN access it
    admin_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    allowed_res = await async_client.get("/api/v1/admin/health", headers=admin_headers)
    assert allowed_res.status_code == 200
    health_data = allowed_res.json()
    assert health_data["role"] == "admin"
    assert health_data["active_clients"] == 3

@pytest.mark.asyncio
async def test_client_isolation_boundaries(async_client: AsyncClient):
    """
    Test Rule 15: Client 1 cannot query or access Client 2 profile/metadata.
    """
    # Login as Client 1
    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_token = c1_login.json()["access_token"]
    c1_headers = {"Authorization": f"Bearer {c1_token}"}

    # Client 1 accessing client_1 profile -> Allowed (200)
    c1_profile = await async_client.get("/api/v1/client/client_1/profile", headers=c1_headers)
    assert c1_profile.status_code == 200
    assert c1_profile.json()["client_id"] == "client_1"

    # Client 1 attempting to access client_2 profile -> Forbidden (403)
    violation_attempt = await async_client.get("/api/v1/client/client_2/profile", headers=c1_headers)
    assert violation_attempt.status_code == 403
    assert "Private boundary violation" in violation_attempt.json()["detail"]

@pytest.mark.asyncio
async def test_model_availability_empty_state(async_client: AsyncClient):
    """
    Test Rule 9 & Rule 47 Stage 1:
    When no models have been published by Admin (all models are draft/none), Client gets empty model list.
    """
    # 1. Admin ensures all registered models are in draft status
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    admin_models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    for m in admin_models_res.json():
        if m["status"] != "draft":
            await async_client.patch(
                f"/api/v1/admin/models/{m['id']}/status",
                json={"status": "draft"},
                headers=admin_headers
            )

    # 2. Client queries models -> must receive empty list []
    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/client/models", headers=c1_headers)
    assert models_res.status_code == 200
    available_models = models_res.json()
    assert available_models == []  # Empty state strictly verified!
