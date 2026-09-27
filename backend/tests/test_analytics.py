import pytest
from httpx import AsyncClient
from app.services.analytics_service import compute_fl_baseline_vs_proposed_analytics

def test_compute_fl_baseline_vs_proposed_analytics():
    """
    Test Section 33 comparative evaluation between Baseline FedAvg and Proposed Platform.
    """
    data = compute_fl_baseline_vs_proposed_analytics("diabetes_prediction")

    metrics = data["metrics_summary"]
    # 1. Higher accuracy
    assert metrics["final_accuracy"]["proposed"] > metrics["final_accuracy"]["baseline"]
    assert metrics["final_accuracy"]["improvement_percent"] > 5.0

    # 2. Lower loss
    assert metrics["final_loss"]["proposed"] < metrics["final_loss"]["baseline"]

    # 3. Communication bandwidth reduction (> 70%)
    assert metrics["communication_mb"]["reduction_percent"] > 70.0

    # 4. Anomaly attack robustness
    assert metrics["attack_resilience"]["proposed_accuracy_under_attack"] > 0.80
    assert metrics["attack_resilience"]["baseline_accuracy_under_attack"] < 0.55

    # 5. Convergence Trajectory
    assert len(data["convergence_trajectory"]) == 5
    for pt in data["convergence_trajectory"]:
        assert pt["proposed_accuracy"] >= pt["baseline_accuracy"]

@pytest.mark.asyncio
async def test_admin_analytics_endpoints(async_client: AsyncClient):
    """
    Test Admin Analytics REST endpoints for comparison matrix and viva defense export.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 1. Comparison endpoint
    cmp_res = await async_client.get(
        "/api/v1/admin/analytics/comparison?task=diabetes_prediction",
        headers=admin_headers
    )
    assert cmp_res.status_code == 200
    cmp_data = cmp_res.json()
    assert "metrics_summary" in cmp_data
    assert "convergence_trajectory" in cmp_data

    # 2. Export Viva Defense Summary
    exp_res = await async_client.get(
        "/api/v1/admin/analytics/export-summary?task=diabetes_prediction",
        headers=admin_headers
    )
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert "project_title" in exp_data
    assert len(exp_data["defense_key_points"]) >= 5
