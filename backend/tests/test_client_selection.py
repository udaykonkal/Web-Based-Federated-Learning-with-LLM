import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.entities import Experiment, MLModel, ClientParticipation, FLRound
from app.services.selection_service import (
    compute_client_selection_scores,
    select_clients_for_round,
    SELECTION_WEIGHTS
)

@pytest.mark.asyncio
async def test_client_selection_scoring_formula():
    """
    Test Section 28 mathematical scoring formula across all 7 constituent factors.
    """
    async with AsyncSessionLocal() as session:
        # Fetch or verify experiment
        m_res = await session.execute(select(MLModel).where(MLModel.healthcare_task == "diabetes_prediction"))
        model = m_res.scalars().first()

        exp = Experiment(
            name="Scoring Formula Unit Test",
            model_id=model.id,
            total_rounds=3,
            client_selection_mode="adaptive",
            local_epochs=2
        )
        exp.model = model
        session.add(exp)
        await session.commit()
        await session.refresh(exp)

        scores = await compute_client_selection_scores(exp, session)

        assert "client_1" in scores
        assert "client_2" in scores
        assert "client_3" in scores

        # Verify factor keys exist for each hospital
        for c_id, data in scores.items():
            assert "composite_score" in data
            factors = data["factors"]
            assert "performance" in factors
            assert "sample_count" in factors
            assert "reliability" in factors
            assert "data_quality" in factors
            assert "comm_cost" in factors
            assert "risk" in factors
            assert "fairness_penalty" in factors

            # Hospital A has 345 samples (max), so sample_count factor must be 1.0
            if c_id == "client_1":
                assert factors["sample_count"] == 1.0

@pytest.mark.asyncio
async def test_adaptive_vs_random_selection():
    """
    Test adaptive ranking selection vs random selection and adaptive weight normalization.
    """
    async with AsyncSessionLocal() as session:
        m_res = await session.execute(select(MLModel).where(MLModel.healthcare_task == "diabetes_prediction"))
        model = m_res.scalars().first()

        exp = Experiment(
            name="Adaptive vs Random Test",
            model_id=model.id,
            total_rounds=3,
            client_selection_mode="adaptive",
            local_epochs=2
        )
        exp.model = model
        session.add(exp)
        await session.commit()

        # 1. Adaptive selection of top 2
        selected, weights, all_scores = await select_clients_for_round(
            experiment=exp,
            db=session,
            mode="adaptive",
            clients_to_select=2
        )
        assert len(selected) == 2
        assert len(weights) == 2
        # Weights should sum approximately to 1.0
        assert 0.99 <= sum(weights.values()) <= 1.01

        # 2. Random selection
        rand_selected, rand_weights, _ = await select_clients_for_round(
            experiment=exp,
            db=session,
            mode="random",
            clients_to_select=2
        )
        assert len(rand_selected) == 2

@pytest.mark.asyncio
async def test_fairness_penalty_adjustment():
    """
    Test that clients with disproportionate participation incur a fairness penalty.
    """
    async with AsyncSessionLocal() as session:
        m_res = await session.execute(select(MLModel).where(MLModel.healthcare_task == "diabetes_prediction"))
        model = m_res.scalars().first()

        exp = Experiment(
            name="Fairness Penalty Test",
            model_id=model.id,
            total_rounds=5,
            client_selection_mode="adaptive"
        )
        exp.model = model
        session.add(exp)
        await session.flush()

        # Create 3 rounds where Client 1 participated 3 times, Client 2 once, Client 3 zero
        for r_num in [1, 2, 3]:
            fl_round = FLRound(experiment_id=exp.id, round_number=r_num, status="completed")
            session.add(fl_round)
            await session.flush()

            # Client 1 participated in all 3
            session.add(ClientParticipation(round_id=fl_round.id, client_id="client_1", is_selected=True, is_accepted=True))
            if r_num == 1:
                session.add(ClientParticipation(round_id=fl_round.id, client_id="client_2", is_selected=True, is_accepted=True))

        await session.commit()

        scores = await compute_client_selection_scores(exp, session)
        # Client 1 has 3 participations while mean is 4/3 = 1.33. Client 1 should have negative penalty
        assert scores["client_1"]["factors"]["fairness_penalty"] < 0.0

@pytest.mark.asyncio
async def test_get_experiment_client_scores_api(async_client: AsyncClient):
    """
    Test REST endpoint for querying real-time client selection scores and breakdowns.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    models_res = await async_client.get("/api/v1/admin/models", headers=admin_headers)
    model = models_res.json()[0]
    if model["status"] not in ["published", "active"]:
        patch_res = await async_client.patch(
            f"/api/v1/admin/models/{model['id']}/status",
            json={"status": "published"},
            headers=admin_headers
        )
        model = patch_res.json()

    exp_res = await async_client.post(
        "/api/v1/admin/experiments",
        json={
            "name": "API Scores Endpoint Test",
            "healthcare_task": model["healthcare_task"],
            "model_id": model["id"],
            "total_rounds": 2,
            "strategy": "FedAvg",
            "client_selection_mode": "adaptive",
            "local_epochs": 1
        },
        headers=admin_headers
    )
    exp_id = exp_res.json()["id"]

    scores_res = await async_client.get(f"/api/v1/admin/experiments/{exp_id}/client-scores", headers=admin_headers)
    assert scores_res.status_code == 200
    scores = scores_res.json()

    assert "client_1" in scores
    assert "client_2" in scores
    assert "client_3" in scores
    assert "factors" in scores["client_1"]
