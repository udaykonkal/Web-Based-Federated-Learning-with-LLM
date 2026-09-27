import pytest
from httpx import AsyncClient
from app.services.llm_service import (
    generate_client_selection_advisory,
    generate_security_threat_advisory,
    generate_hyperparameter_advisory
)

def test_client_selection_advisory():
    """
    Test Section 32 automated client selection advisor logic and structured schema.
    """
    candidate_scores = {
        "client_1": {"composite_score": 0.78, "factors": {"performance": 0.85}},
        "client_2": {"composite_score": 0.65, "factors": {"performance": 0.72}},
        "client_3": {"composite_score": 0.35, "factors": {"performance": 0.50}},
    }
    advisory = generate_client_selection_advisory(candidate_scores, "diabetes_prediction")

    assert len(advisory.selected_clients) == 2
    assert "client_1" in advisory.selected_clients
    assert advisory.confidence >= 0.85
    assert advisory.generated_by in ["deterministic_fallback", "llm_reasoning"]
    assert len(advisory.risk_assessment) == 3

def test_security_threat_advisory_clean_and_attack():
    """
    Test Section 32 automated security threat advisory.
    """
    clean_updates = [
        {"client_id": "client_1", "update_norm": 1.2, "anomaly_score": 0.1, "cosine_similarity": 0.95},
        {"client_id": "client_2", "update_norm": 1.1, "anomaly_score": 0.15, "cosine_similarity": 0.92},
    ]
    clean_adv = generate_security_threat_advisory(clean_updates)
    assert clean_adv.threat_level == "LOW"
    assert len(clean_adv.flagged_clients) == 0

    attack_updates = [
        {"client_id": "client_1", "update_norm": 1.2, "anomaly_score": 0.1, "cosine_similarity": 0.95},
        {"client_id": "client_3", "update_norm": 1.4, "anomaly_score": 0.85, "cosine_similarity": -0.65},
    ]
    attack_adv = generate_security_threat_advisory(attack_updates)
    assert attack_adv.threat_level in ["HIGH", "CRITICAL"]
    assert "client_3" in attack_adv.flagged_clients
    assert "REJECT" in attack_adv.recommended_actions.get("Hospital C", "")

def test_hyperparameter_advisory():
    """
    Test Section 32 automated hyperparameter tuning advisor.
    """
    # Plateau history -> Early stopping recommendation
    plateau_history = [
        {"round_number": 1, "global_loss": 0.4500, "global_accuracy": 0.8200},
        {"round_number": 2, "global_loss": 0.4200, "global_accuracy": 0.8400},
        {"round_number": 3, "global_loss": 0.4190, "global_accuracy": 0.8410},
    ]
    adv = generate_hyperparameter_advisory(plateau_history, current_lr=0.01, current_epochs=3)
    assert adv.early_stopping is True

    # Diverging history -> Reduce learning rate
    diverging_history = [
        {"round_number": 1, "global_loss": 0.4200, "global_accuracy": 0.8400},
        {"round_number": 2, "global_loss": 0.5100, "global_accuracy": 0.7600},
    ]
    adv_div = generate_hyperparameter_advisory(diverging_history, current_lr=0.01, current_epochs=3)
    assert adv_div.recommended_lr < 0.01
    assert adv_div.early_stopping is False

@pytest.mark.asyncio
async def test_admin_llm_endpoints(async_client: AsyncClient):
    """
    Test Admin LLM REST advisor endpoints.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 1. Client selection advisory
    sel_res = await async_client.post(
        "/api/v1/admin/llm/client-selection-advisor",
        json={"healthcare_task": "diabetes_prediction"},
        headers=admin_headers
    )
    assert sel_res.status_code == 200
    sel_data = sel_res.json()
    assert "selected_clients" in sel_data
    assert "confidence" in sel_data

    # 2. Security threat advisory
    sec_res = await async_client.post(
        "/api/v1/admin/llm/security-threat-advisor",
        json={},
        headers=admin_headers
    )
    assert sec_res.status_code == 200
    sec_data = sec_res.json()
    assert "threat_level" in sec_data

    # 3. Hyperparameter advisory
    hyp_res = await async_client.post(
        "/api/v1/admin/llm/hyperparameter-advisor",
        json={"learning_rate": 0.01, "local_epochs": 3},
        headers=admin_headers
    )
    assert hyp_res.status_code == 200
    hyp_data = hyp_res.json()
    assert "recommended_lr" in hyp_data
    assert "early_stopping" in hyp_data
