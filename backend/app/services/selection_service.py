from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.entities import Experiment, FLRound, ClientParticipation, ModelUpdate, Client, MLModel
from app.services.client_data_service import get_client_partition_metadata

# Section 28 Standard Weights: w1 + w2 + w3 + w4 + w5 + w6 = 1.0, lambda = 0.10
SELECTION_WEIGHTS = {
    "w_perf": 0.25,        # Performance (local accuracy/F1)
    "w_sample": 0.20,      # Sample count ratio
    "w_reliability": 0.15, # Historical participation rate
    "w_quality": 0.15,     # Data quality / class balance
    "w_comm": 0.10,        # Network / communication cost
    "w_risk": 0.15,        # Anomaly / rejection risk
    "lambda_fairness": 0.10 # Fairness regularizer
}

async def compute_client_selection_scores(
    experiment: Optional[Experiment] = None,
    db: Optional[AsyncSession] = None,
    healthcare_task: str = "diabetes_prediction"
) -> Dict[str, Dict[str, Any]]:
    """
    Multi-Factor Adaptive Client Selection Formula (Section 28):
      Score_k = w1*Perf + w2*Samples + w3*Reliability + w4*DataQuality - w5*CommCost - w6*Risk + lambda*FairnessPenalty
    """
    client_ids = ["client_1", "client_2", "client_3"]
    scores_dict: Dict[str, Dict[str, Any]] = {}

    # 1. Fetch historical participation counts for fairness calculation
    part_counts: Dict[str, int] = {}
    if experiment is not None and db is not None:
        for c_id in client_ids:
            res = await db.execute(
                select(func.count(ClientParticipation.id))
                .join(FLRound)
                .where(
                    FLRound.experiment_id == experiment.id,
                    ClientParticipation.client_id == c_id,
                    ClientParticipation.is_selected == True
                )
            )
            part_counts[c_id] = res.scalar() or 0
    else:
        part_counts = {c: 0 for c in client_ids}

    mean_participation = np.mean(list(part_counts.values())) if part_counts else 0.0

    # 2. Get partition metadata for sample counts and class balance
    task = healthcare_task
    if experiment is not None and experiment.model_id and db is not None:
        task_res = await db.execute(select(MLModel.healthcare_task).where(MLModel.id == experiment.model_id))
        t = task_res.scalar()
        if t:
            task = t
    metadata = get_client_partition_metadata(task)
    max_samples = max(meta["total_records"] for meta in metadata.values())

    for c_id in client_ids:
        meta = metadata.get(c_id, {"total_records": 200, "class_balance": {0: 100, 1: 100}})
        n_k = meta["total_records"]

        # Factor 1: Performance_k (from latest round or baseline 0.75)
        if experiment is not None and db is not None:
            perf_res = await db.execute(
                select(ClientParticipation.local_accuracy)
                .join(FLRound)
                .where(
                    FLRound.experiment_id == experiment.id,
                    ClientParticipation.client_id == c_id
                )
                .order_by(FLRound.round_number.desc())
                .limit(1)
            )
            latest_acc = perf_res.scalar()
            perf_k = float(latest_acc) if latest_acc is not None else 0.75
        else:
            perf_k = 0.75

        # Factor 2: SampleCount_k (normalized 0 to 1)
        sample_k = n_k / max_samples

        # Factor 3: Reliability_k (rounds accepted / rounds invited)
        if experiment is not None and db is not None:
            total_invites_res = await db.execute(
                select(func.count(ClientParticipation.id))
                .join(FLRound)
                .where(
                    FLRound.experiment_id == experiment.id,
                    ClientParticipation.client_id == c_id
                )
            )
            total_invites = total_invites_res.scalar() or 0

            accepted_res = await db.execute(
                select(func.count(ClientParticipation.id))
                .join(FLRound)
                .where(
                    FLRound.experiment_id == experiment.id,
                    ClientParticipation.client_id == c_id,
                    ClientParticipation.is_accepted == True
                )
            )
            total_accepted = accepted_res.scalar() or 0
            reliability_k = (total_accepted / total_invites) if total_invites > 0 else 1.0
        else:
            reliability_k = 1.0

        # Factor 4: DataQuality_k (Class balance score based on minority class ratio)
        balance = meta.get("class_balance", {})
        counts = list(balance.values()) if balance else [1, 1]
        minority_ratio = min(counts) / max(counts) if max(counts) > 0 else 0.5
        # Scale to 0.5 - 1.0
        quality_k = min(1.0, max(0.0, minority_ratio * 1.5))

        # Factor 5: CommCost_k (Estimated communication delay based on partition size)
        # Client 1 (largest) = 0.35, Client 2 = 0.25, Client 3 = 0.15
        comm_cost_k = 0.15 + 0.20 * sample_k

        # Factor 6: Risk_k (Historical anomaly/rejection score)
        if experiment is not None and db is not None:
            risk_res = await db.execute(
                select(func.count(ModelUpdate.id))
                .join(FLRound)
                .where(
                    FLRound.experiment_id == experiment.id,
                    ModelUpdate.client_id == c_id,
                    ModelUpdate.is_rejected == True
                )
            )
            rejected_count = risk_res.scalar() or 0
            risk_k = min(1.0, rejected_count * 0.5)
        else:
            risk_k = 0.05

        # Factor 7: FairnessPenalty_k = -((r_k / mean_r) - 1)^2
        r_k = part_counts[c_id]
        if mean_participation > 0:
            fairness_penalty_k = - float(((r_k / mean_participation) - 1.0) ** 2)
        else:
            fairness_penalty_k = 0.0

        # Calculate final composite score
        composite_score = (
            SELECTION_WEIGHTS["w_perf"] * perf_k +
            SELECTION_WEIGHTS["w_sample"] * sample_k +
            SELECTION_WEIGHTS["w_reliability"] * reliability_k +
            SELECTION_WEIGHTS["w_quality"] * quality_k -
            SELECTION_WEIGHTS["w_comm"] * comm_cost_k -
            SELECTION_WEIGHTS["w_risk"] * risk_k +
            SELECTION_WEIGHTS["lambda_fairness"] * fairness_penalty_k
        )

        scores_dict[c_id] = {
            "composite_score": round(composite_score, 4),
            "factors": {
                "performance": round(perf_k, 4),
                "sample_count": round(sample_k, 4),
                "reliability": round(reliability_k, 4),
                "data_quality": round(quality_k, 4),
                "comm_cost": round(comm_cost_k, 4),
                "risk": round(risk_k, 4),
                "fairness_penalty": round(fairness_penalty_k, 4)
            },
            "raw_samples": n_k,
            "participation_count": r_k
        }

    return scores_dict

async def select_clients_for_round(
    experiment: Experiment,
    db: AsyncSession,
    mode: str = "adaptive",
    clients_to_select: int = 3
) -> Tuple[List[str], Dict[str, float], Dict[str, Dict[str, Any]]]:
    """
    Select participating clients for an FL round (Section 28).
    Returns:
      - selected_client_ids: list of chosen client IDs
      - adaptive_weights: normalized positive scoring weights for aggregation
      - all_scores_breakdown: full factor breakdown for each candidate client
    """
    all_scores = await compute_client_selection_scores(experiment, db)
    client_ids = list(all_scores.keys())

    if mode == "random":
        # Baseline Strategy: uniform random selection
        np.random.seed(experiment.current_round + 42)
        k = min(clients_to_select, len(client_ids))
        selected = list(np.random.choice(client_ids, size=k, replace=False))
    else:
        # Proposed Strategy: Rank by composite score and select top K
        sorted_clients = sorted(client_ids, key=lambda c: all_scores[c]["composite_score"], reverse=True)
        selected = sorted_clients[:clients_to_select]

    # Calculate normalized positive adaptive weights for the selected clients
    min_score = min(all_scores[c]["composite_score"] for c in selected)
    # Shift to strictly positive range for weighting
    shift = abs(min_score) + 0.1 if min_score <= 0 else 0.0
    shifted_scores = {c: all_scores[c]["composite_score"] + shift for c in selected}
    total_shifted = sum(shifted_scores.values())

    adaptive_weights = {c: round(shifted_scores[c] / total_shifted, 4) for c in selected}

    return selected, adaptive_weights, all_scores
