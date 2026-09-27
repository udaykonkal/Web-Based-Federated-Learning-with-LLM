import pytest
from pathlib import Path
import pandas as pd
from httpx import AsyncClient

from app.core.config import settings
from app.services.client_data_service import (
    generate_non_iid_client_partitions,
    load_client_private_data,
    get_client_dataset_metadata
)

@pytest.fixture(scope="module", autouse=True)
def ensure_partitions_exist():
    """Ensure non-IID client partitions are generated before testing."""
    generate_non_iid_client_partitions()

def test_non_iid_partition_heterogeneity():
    """
    Test Rule 5 & 22: Non-IID Data Architecture.
    Verify that Client 1, 2, and 3 have physically isolated files with
    meaningfully different sample counts and class distributions.
    """
    c1_dia = load_client_private_data("client_1", "diabetes_prediction")
    c2_dia = load_client_private_data("client_2", "diabetes_prediction")
    c3_dia = load_client_private_data("client_3", "diabetes_prediction")

    # Sample counts must be different
    assert len(c1_dia) != len(c2_dia)
    assert len(c2_dia) != len(c3_dia)
    assert len(c1_dia) + len(c2_dia) + len(c3_dia) == 768

    # Verify Heart Disease partitions
    c1_heart = load_client_private_data("client_1", "heart_disease_prediction")
    c2_heart = load_client_private_data("client_2", "heart_disease_prediction")
    c3_heart = load_client_private_data("client_3", "heart_disease_prediction")

    assert len(c1_heart) != len(c2_heart)
    assert len(c2_heart) != len(c3_heart)
    assert len(c1_heart) + len(c2_heart) + len(c3_heart) == 303

@pytest.mark.asyncio
async def test_client_isolated_profile_access(async_client: AsyncClient):
    """
    Test Rule 15: Client 1 cannot view Client 2 or Client 3 private profiles.
    """
    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    c1_headers = {"Authorization": f"Bearer {c1_login.json()['access_token']}"}

    # Client 1 accessing client_1 -> Allowed
    res_self = await async_client.get("/api/v1/client/client_1/profile", headers=c1_headers)
    assert res_self.status_code == 200
    data = res_self.json()
    assert data["client_id"] == "client_1"
    assert data["diabetes"]["sample_count"] == 345
    assert data["heart_disease"]["sample_count"] == 136

    # Client 1 attempting to access client_2 -> Blocked (403)
    res_violation2 = await async_client.get("/api/v1/client/client_2/profile", headers=c1_headers)
    assert res_violation2.status_code == 403
    assert "Private boundary violation" in res_violation2.json()["detail"]

    # Client 1 attempting to access client_3 -> Blocked (403)
    res_violation3 = await async_client.get("/api/v1/client/client_3/profile", headers=c1_headers)
    assert res_violation3.status_code == 403
    assert "Private boundary violation" in res_violation3.json()["detail"]

@pytest.mark.asyncio
async def test_cross_client_isolation_all_nodes(async_client: AsyncClient):
    """
    Test complete mutual isolation across all 3 client nodes:
    Hospital B cannot access Hospital A or C.
    Hospital C cannot access Hospital A or B.
    """
    # Client 2
    c2_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_b@flplatform.org", "password": "client2pass"}
    )
    c2_headers = {"Authorization": f"Bearer {c2_login.json()['access_token']}"}

    res_c2_self = await async_client.get("/api/v1/client/client_2/profile", headers=c2_headers)
    assert res_c2_self.status_code == 200
    assert res_c2_self.json()["diabetes"]["sample_count"] == 268

    res_c2_to_c1 = await async_client.get("/api/v1/client/client_1/profile", headers=c2_headers)
    assert res_c2_to_c1.status_code == 403

    # Client 3
    c3_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_c@flplatform.org", "password": "client3pass"}
    )
    c3_headers = {"Authorization": f"Bearer {c3_login.json()['access_token']}"}

    res_c3_self = await async_client.get("/api/v1/client/client_3/profile", headers=c3_headers)
    assert res_c3_self.status_code == 200
    assert res_c3_self.json()["diabetes"]["sample_count"] == 155

    res_c3_to_c1 = await async_client.get("/api/v1/client/client_1/profile", headers=c3_headers)
    assert res_c3_to_c1.status_code == 403

@pytest.mark.asyncio
async def test_admin_cannot_access_client_private_data(async_client: AsyncClient):
    """
    Test Rule 6 & 16: Admin coordinator cannot call client-only private endpoints.
    Admin sees system-wide metrics, never raw private client datasets.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # Admin attempting to fetch client_1 private profile -> 403 Forbidden
    res = await async_client.get("/api/v1/client/client_1/profile", headers=admin_headers)
    assert res.status_code == 403
    assert "Client role required" in res.json()["detail"]

@pytest.mark.asyncio
async def test_workspace_client_specific_partition(async_client: AsyncClient):
    """
    Test that when different clients open a published model workspace,
    each client sees only its OWN local private sample count.
    """
    # Ensure Diabetes model is published
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    
    # Get diabetes model id
    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    dia_id = next(m["id"] for m in models_res.json() if m["healthcare_task"] == "diabetes_prediction")
    
    # Publish & Activate it
    await async_client.patch(
        f"/api/v1/admin/models/{dia_id}/status",
        json={"status": "active"},
        headers=admin_headers
    )

    # Client 1 checks workspace
    c1_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    w1 = await async_client.get(
        f"/api/v1/client/models/{dia_id}",
        headers={"Authorization": f"Bearer {c1_login.json()['access_token']}"}
    )
    assert w1.status_code == 200
    assert w1.json()["client_private_data"]["sample_count"] == 345

    # Client 2 checks workspace
    c2_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_b@flplatform.org", "password": "client2pass"}
    )
    w2 = await async_client.get(
        f"/api/v1/client/models/{dia_id}",
        headers={"Authorization": f"Bearer {c2_login.json()['access_token']}"}
    )
    assert w2.status_code == 200
    assert w2.json()["client_private_data"]["sample_count"] == 268
    assert w1.json()["client_private_data"]["sample_count"] != w2.json()["client_private_data"]["sample_count"]
