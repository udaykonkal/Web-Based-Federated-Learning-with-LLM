import pytest
import torch
from httpx import AsyncClient
from app.services.security_service import (
    apply_simulated_attack,
    verify_and_score_updates,
    compute_coordinate_median_weights
)

def create_mock_updates():
    """Create 3 synthetic client updates mimicking local training gradients."""
    u1 = {"client_id": "client_1", "delta_weights": {"w": torch.tensor([0.1, 0.2, 0.3])}, "sample_count": 345, "accuracy": 0.80, "loss": 0.45}
    u2 = {"client_id": "client_2", "delta_weights": {"w": torch.tensor([0.12, 0.19, 0.28])}, "sample_count": 268, "accuracy": 0.78, "loss": 0.47}
    u3 = {"client_id": "client_3", "delta_weights": {"w": torch.tensor([0.09, 0.22, 0.31])}, "sample_count": 155, "accuracy": 0.75, "loss": 0.50}
    return [u1, u2, u3]

def test_clean_updates_accepted():
    """
    Test that honest, benign client updates pass mathematical screening without rejection.
    """
    updates = create_mock_updates()
    verified = verify_and_score_updates(updates)

    for v in verified:
        assert v["is_rejected"] is False
        assert v["security_action"] in ["ACCEPTED", "DOWN_WEIGHTED"]
        assert v["anomaly_score"] < 0.55
        assert v["cosine_similarity"] > 0.80

def test_sign_flipping_attack_detection():
    """
    Test Section 30 sign-flipping attack detection (inverted gradients).
    """
    updates = create_mock_updates()
    # Poison Client 3 with sign-flipping
    poisoned, _ = apply_simulated_attack(updates[2]["delta_weights"], "sign_flipping", severity=1.0)
    updates[2]["delta_weights"] = poisoned

    verified = verify_and_score_updates(updates)
    attacker = next(v for v in verified if v["client_id"] == "client_3")

    assert attacker["is_rejected"] is True
    assert attacker["security_action"] == "REJECTED"
    assert attacker["cosine_similarity"] < 0.0

def test_extreme_scaling_attack_detection():
    """
    Test Section 30 scaling/free-rider attack detection (exaggerated norm).
    """
    updates = create_mock_updates()
    poisoned, _ = apply_simulated_attack(updates[2]["delta_weights"], "scaling", severity=2.0)
    updates[2]["delta_weights"] = poisoned

    verified = verify_and_score_updates(updates, norm_threshold=2.0)
    attacker = next(v for v in verified if v["client_id"] == "client_3")

    assert attacker["is_rejected"] is True
    assert attacker["security_action"] == "REJECTED"
    assert attacker["update_norm"] > 2.0

def test_gaussian_noise_attack_detection():
    """
    Test Section 30 Gaussian noise injection detection (divergent variance).
    """
    updates = create_mock_updates()
    # Create large parameter vector to measure variance reliably
    for u in updates:
        u["delta_weights"]["big_w"] = torch.ones(100) * 0.1
    poisoned, _ = apply_simulated_attack(updates[2]["delta_weights"], "gaussian_noise", severity=2.0)
    updates[2]["delta_weights"] = poisoned

    verified = verify_and_score_updates(updates)
    attacker = next(v for v in verified if v["client_id"] == "client_3")

    assert attacker["is_rejected"] is True
    assert attacker["anomaly_score"] > 0.50

@pytest.mark.asyncio
async def test_security_overview_and_simulation_api(async_client: AsyncClient):
    """
    Test Admin Security REST endpoints for overview and attack simulation.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 1. Overview
    overview_res = await async_client.get("/api/v1/admin/security/overview", headers=admin_headers)
    assert overview_res.status_code == 200
    ov_data = overview_res.json()
    assert "total_screened_updates" in ov_data
    assert "defense_policy" in ov_data

    # 2. Simulate Attack
    sim_res = await async_client.post(
        "/api/v1/admin/security/simulate-attack",
        json={
            "client_id": "client_3",
            "attack_type": "sign_flipping",
            "severity": 1.0,
            "task": "diabetes_prediction"
        },
        headers=admin_headers
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["simulated_attack"]["detected"] is True
    assert sim_data["simulated_attack"]["action_taken"] == "REJECTED"
    assert len(sim_data["all_screened_nodes"]) == 3
