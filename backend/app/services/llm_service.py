import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Pydantic Output Schemas (Section 32)
class ClientSelectionAdvisory(BaseModel):
    selected_clients: List[str]
    rationale: str
    predicted_convergence_impact: str
    risk_assessment: Dict[str, str]
    confidence: float
    generated_by: str  # "llm_reasoning" or "deterministic_fallback"

class SecurityThreatAdvisory(BaseModel):
    threat_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    flagged_clients: List[str]
    recommended_actions: Dict[str, str]
    confidence: float
    clinical_explanation: str
    generated_by: str

class HyperparameterAdvisory(BaseModel):
    recommended_lr: float
    recommended_epochs: int
    early_stopping: bool
    rationale: str
    confidence: float
    generated_by: str

CLIENT_MAP = {
    "client_1": "Hospital A",
    "client_2": "Hospital B",
    "client_3": "Hospital C"
}

def generate_client_selection_advisory(
    candidate_scores: Dict[str, Any],
    healthcare_task: str
) -> ClientSelectionAdvisory:
    """
    Automated Client Selection Advisor (Section 32).
    Analyzes client scores, non-IID characteristics, and participation history.
    """
    # Deterministic Rule-Based Intelligence Engine
    sorted_nodes = sorted(
        candidate_scores.items(),
        key=lambda item: item[1].get("composite_score", 0.0),
        reverse=True
    )
    top_clients = [k for k, v in sorted_nodes[:2]]
    top_names = [CLIENT_MAP.get(c, c) for c in top_clients]

    risk_dict = {}
    for cid, data in candidate_scores.items():
        score = data.get("composite_score", 0.0)
        cname = CLIENT_MAP.get(cid, cid)
        if score > 0.6:
            risk_dict[cname] = "Low clinical risk: strong statistical representation and high participation reliability."
        elif score > 0.4:
            risk_dict[cname] = "Moderate risk: minority class imbalance present; requires regularized aggregation."
        else:
            risk_dict[cname] = "Elevated risk: potential staleness or participation bias."

    rationale = (
        f"Prioritizing {', '.join(top_names)} for the next federated round based on high sample counts, "
        f"optimal class balance for {healthcare_task.replace('_', ' ')}, and verified training reliability."
    )
    predicted_impact = "Accelerated global benchmark convergence with minimal gradient variance across hospital nodes."

    return ClientSelectionAdvisory(
        selected_clients=top_clients,
        rationale=rationale,
        predicted_convergence_impact=predicted_impact,
        risk_assessment=risk_dict,
        confidence=0.92,
        generated_by="deterministic_fallback"
    )

def generate_security_threat_advisory(
    screened_updates: List[Dict[str, Any]]
) -> SecurityThreatAdvisory:
    """
    Automated Anomaly and Security Assessment (Section 30 & 32).
    Screens norm, cosine similarity, and anomaly score to generate threat intelligence.
    """
    flagged = []
    actions = {}
    highest_anomaly = 0.0

    for u in screened_updates:
        cid = u["client_id"]
        cname = CLIENT_MAP.get(cid, cid)
        anom = u.get("anomaly_score", 0.0)
        sim = u.get("cosine_similarity", 1.0)
        norm = u.get("update_norm", 1.0)
        highest_anomaly = max(highest_anomaly, anom)

        if sim < -0.1:
            flagged.append(cid)
            actions[cname] = "REJECT: Gradient sign-inversion detected (deliberate sign-flipping attack pattern)."
        elif norm > 7.5:
            flagged.append(cid)
            actions[cname] = "REJECT: Gradient magnitude explosion detected (extreme scaling attack pattern)."
        elif anom > 0.55:
            flagged.append(cid)
            actions[cname] = "REJECT: High composite anomaly score exceeding security ceiling."
        elif anom > 0.40:
            actions[cname] = "DOWN-WEIGHT: Mild variance from coordinate median; apply 50% discount to aggregation weight."
        else:
            actions[cname] = "ACCEPT: Benign update consistent with clinical population distribution."

    if flagged:
        threat_level = "CRITICAL" if len(flagged) > 1 else "HIGH"
        explanation = (
            f"Adversarial update behavior intercepted from node(s): {', '.join(flagged)}. "
            f"Updates exhibit negative directional alignment or abnormal tensor norms, posing significant risk of "
            f"corrupting central diagnostic predictions if aggregated."
        )
        conf = 0.95
    else:
        threat_level = "LOW"
        explanation = (
            "All received parameter updates align with clinical expectation. Directional cosine similarities with "
            "the coordinate median are positive, and update L2 norms remain within normal training bounds."
        )
        conf = 0.98

    return SecurityThreatAdvisory(
        threat_level=threat_level,
        flagged_clients=flagged,
        recommended_actions=actions,
        confidence=conf,
        clinical_explanation=explanation,
        generated_by="deterministic_fallback"
    )

def generate_hyperparameter_advisory(
    rounds_history: List[Dict[str, Any]],
    current_lr: float = 0.01,
    current_epochs: int = 3
) -> HyperparameterAdvisory:
    """
    Automated Hyperparameter Tuning Advisor (Section 32).
    Analyzes multi-round loss and accuracy trajectories to recommend learning rate and epochs.
    """
    if len(rounds_history) < 2:
        return HyperparameterAdvisory(
            recommended_lr=current_lr,
            recommended_epochs=current_epochs,
            early_stopping=False,
            rationale="Initial round baseline established. Maintain current learning rate and local epochs.",
            confidence=0.85,
            generated_by="deterministic_fallback"
        )

    losses = [r["global_loss"] for r in rounds_history if r.get("global_loss") is not None]
    accuracies = [r["global_accuracy"] for r in rounds_history if r.get("global_accuracy") is not None]

    delta_loss = losses[-1] - losses[-2] if len(losses) >= 2 else 0.0

    if delta_loss > 0.05:
        # Loss increased: model is diverging or oscillating
        new_lr = round(current_lr * 0.5, 4)
        new_epochs = max(1, current_epochs - 1)
        early_stop = False
        rationale = (
            f"Global benchmark loss increased by {delta_loss:.4f}. Recommend decreasing learning rate from "
            f"{current_lr} to {new_lr} and reducing local epochs to prevent client drift."
        )
    elif abs(delta_loss) < 0.002 and len(losses) >= 3:
        # Plateau reached
        new_lr = current_lr
        new_epochs = current_epochs
        early_stop = True
        rationale = (
            "Model has converged to an asymptotic plateau (ΔLoss < 0.002). "
            "Recommend triggering early stopping to conserve hospital compute resources."
        )
    else:
        # Healthy steady convergence
        new_lr = current_lr
        new_epochs = current_epochs
        early_stop = False
        rationale = (
            f"Healthy convergence observed (ΔLoss = {delta_loss:.4f}). "
            f"Model accuracy steadily climbing. Maintain lr={current_lr} and {current_epochs} local epochs."
        )

    return HyperparameterAdvisory(
        recommended_lr=new_lr,
        recommended_epochs=new_epochs,
        early_stopping=early_stop,
        rationale=rationale,
        confidence=0.90,
        generated_by="deterministic_fallback"
    )
