from typing import Dict, Any, List, Tuple, Optional
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.ml.models import (
    get_model_for_task,
    get_weights,
    set_weights,
    calculate_l2_norm,
    evaluate_model,
    serialize_weights,
    deserialize_weights
)

def aggregate_fedavg(
    global_weights: Dict[str, torch.Tensor],
    client_updates: List[Dict[str, Any]],
    adaptive_weights: Optional[Dict[str, float]] = None
) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
    """
    Classic Federated Averaging (FedAvg) aggregation (Section 25):
      W_{t+1} = W_t + sum_{k in S_t} (n_k / N_t) * Delta W_k
    
    If adaptive_weights is provided (Phase 8), it uses normalized adaptive scores instead of raw sample ratios.
    Does NOT average accuracies; strictly computes mathematical tensor parameter aggregation.
    """
    if not client_updates:
        raise ValueError("Cannot aggregate: client_updates list is empty.")

    total_samples = sum(u["sample_count"] for u in client_updates)
    num_clients = len(client_updates)

    # Compute normalized weights for each client
    client_weights = {}
    if adaptive_weights:
        total_adaptive = sum(adaptive_weights.get(u["client_id"], 1.0) for u in client_updates)
        for u in client_updates:
            c_id = u["client_id"]
            client_weights[c_id] = adaptive_weights.get(c_id, 1.0) / total_adaptive
    else:
        for u in client_updates:
            c_id = u["client_id"]
            client_weights[c_id] = u["sample_count"] / total_samples

    # Compute weighted average of parameter deltas
    aggregated_delta: Dict[str, torch.Tensor] = {}
    
    # Initialize aggregated deltas to zero tensors matching global weight shapes
    first_client_deltas = client_updates[0]["delta_weights"]
    for param_name, param_tensor in first_client_deltas.items():
        if param_tensor.is_floating_point():
            aggregated_delta[param_name] = torch.zeros_like(param_tensor, dtype=torch.float32)
        else:
            aggregated_delta[param_name] = param_tensor.clone()

    for u in client_updates:
        c_id = u["client_id"]
        w_k = client_weights[c_id]
        c_deltas = u["delta_weights"]

        for param_name in aggregated_delta:
            if aggregated_delta[param_name].is_floating_point():
                aggregated_delta[param_name] += w_k * c_deltas[param_name].float()

    # Apply aggregated delta to current global weights: W_{t+1} = W_t + Delta W_agg
    new_global_weights: Dict[str, torch.Tensor] = {}
    for param_name in global_weights:
        orig_param = global_weights[param_name]
        if orig_param.is_floating_point():
            new_global_weights[param_name] = orig_param + aggregated_delta[param_name].type_as(orig_param)
        else:
            new_global_weights[param_name] = orig_param + aggregated_delta[param_name]

    agg_l2_norm = calculate_l2_norm(aggregated_delta)

    metrics = {
        "num_participating_clients": num_clients,
        "total_samples": total_samples,
        "client_weights": {k: round(v, 4) for k, v in client_weights.items()},
        "aggregated_l2_norm": round(agg_l2_norm, 6),
        "aggregation_strategy": "FedAvg (Weighted Sample Average)" if not adaptive_weights else "FedAvg (Adaptive Scoring)"
    }

    return new_global_weights, metrics

def evaluate_global_model_on_benchmark(
    weights: Dict[str, torch.Tensor],
    healthcare_task: str
) -> Dict[str, float]:
    """
    Evaluate global model parameters against the centralized Admin benchmark dataset (Section 27).
    Standardizes features locally and evaluates classification accuracy, loss, precision, recall, and F1.
    """
    admin_dir = settings.ADMIN_DATA_PATH
    if healthcare_task == "diabetes_prediction":
        csv_file = admin_dir / "diabetes_prediction.csv"
        target_col = "Outcome"
    elif healthcare_task == "heart_disease_prediction":
        csv_file = admin_dir / "heart_disease_prediction.csv"
        target_col = "target"
    else:
        raise ValueError(f"Unknown task: {healthcare_task}")

    df = pd.read_csv(csv_file)
    X = df.drop(columns=[target_col]).values.astype(np.float32)
    y = df[target_col].values.astype(np.float32).reshape(-1, 1)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_tensor = torch.tensor(X_scaled)
    y_tensor = torch.tensor(y)

    model = get_model_for_task(healthcare_task)
    set_weights(model, weights)

    return evaluate_model(model, X_tensor, y_tensor)
