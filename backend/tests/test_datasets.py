import io
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_initialize_benchmark_datasets(async_client: AsyncClient):
    """
    Test that Admin can initialize benchmark datasets for Diabetes and Heart Disease.
    """
    # 1. Login as Admin
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Call initialization
    init_res = await async_client.post(
        "/api/v1/admin/datasets/initialize-benchmarks",
        headers=headers
    )
    assert init_res.status_code == 200
    datasets = init_res.json()
    assert len(datasets) >= 2

    tasks = [d["healthcare_task"] for d in datasets]
    assert "diabetes_prediction" in tasks
    assert "heart_disease_prediction" in tasks

@pytest.mark.asyncio
async def test_list_and_inspect_datasets(async_client: AsyncClient):
    """
    Test listing datasets and inspecting feature counts, records, and class distributions.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    res = await async_client.get("/api/v1/admin/datasets", headers=headers)
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 2

    # Verify Diabetes dataset metadata
    dia = next(d for d in datasets if d["healthcare_task"] == "diabetes_prediction")
    assert dia["name"] == "Diabetes Prediction Dataset"
    assert dia["record_count"] == 768
    assert dia["feature_count"] == 8
    assert dia["target_variable"] == "Outcome"
    assert "0" in dia["class_distribution"]
    assert "1" in dia["class_distribution"]

    # Verify Heart Disease dataset metadata
    heart = next(d for d in datasets if d["healthcare_task"] == "heart_disease_prediction")
    assert heart["name"] == "Heart Disease Prediction Dataset"
    assert heart["record_count"] == 303
    assert heart["feature_count"] == 13
    assert heart["target_variable"] == "target"
    assert "0" in heart["class_distribution"]
    assert "1" in heart["class_distribution"]

@pytest.mark.asyncio
async def test_dataset_detail_and_summary_stats(async_client: AsyncClient):
    """
    Test getting detailed dataset info with summary statistics.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    res = await async_client.get("/api/v1/admin/datasets", headers=headers)
    dia_id = next(d["id"] for d in res.json() if d["healthcare_task"] == "diabetes_prediction")

    detail_res = await async_client.get(f"/api/v1/admin/datasets/{dia_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "summary_stats" in detail
    assert "Glucose" in detail["summary_stats"]
    assert "mean" in detail["summary_stats"]["Glucose"]

@pytest.mark.asyncio
async def test_dataset_status_toggle(async_client: AsyncClient):
    """
    Test activating/deactivating a dataset.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    res = await async_client.get("/api/v1/admin/datasets", headers=headers)
    dataset_id = res.json()[0]["id"]

    # Deactivate
    patch_res = await async_client.patch(
        f"/api/v1/admin/datasets/{dataset_id}/status",
        json={"status": "inactive"},
        headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "inactive"

    # Reactivate
    reactivate_res = await async_client.patch(
        f"/api/v1/admin/datasets/{dataset_id}/status",
        json={"status": "active"},
        headers=headers
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["status"] == "active"

@pytest.mark.asyncio
async def test_invalid_csv_rejected(async_client: AsyncClient):
    """
    Test that uploading an invalid CSV (missing required healthcare columns) is rejected.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # CSV missing required diabetes features
    invalid_csv = "FeatureA,FeatureB,Outcome\n1,2,0\n3,4,1"
    files = {"file": ("invalid.csv", io.BytesIO(invalid_csv.encode("utf-8")), "text/csv")}
    data = {"name": "Invalid Diabetes Dataset", "healthcare_task": "diabetes_prediction"}

    upload_res = await async_client.post(
        "/api/v1/admin/datasets/upload",
        headers=headers,
        data=data,
        files=files
    )
    assert upload_res.status_code == 400
    assert "Missing required healthcare features" in upload_res.json()["detail"]

@pytest.mark.asyncio
async def test_client_forbidden_from_admin_datasets(async_client: AsyncClient):
    """
    Rule 41: A Client token cannot manage Admin datasets.
    """
    client_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hospital_a@flplatform.org", "password": "client1pass"}
    )
    headers = {"Authorization": f"Bearer {client_login.json()['access_token']}"}

    forbidden_res = await async_client.get("/api/v1/admin/datasets", headers=headers)
    assert forbidden_res.status_code == 403
