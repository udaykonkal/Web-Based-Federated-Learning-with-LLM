import math
from typing import Dict, Any, List, Tuple
import torch
import numpy as np

def flatten_weights_dict(weights_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
    """Flatten all floating point tensors in a state dict into a single 1D tensor."""
    tensors = []
    for k, v in sorted(weights_dict.items()):
        if v.is_floating_point():
            tensors.append(v.detach().cpu().view(-1).float())
    if not tensors:
        return torch.tensor([0.0])
    return torch.cat(tensors)

def compute_coordinate_median_weights(client_updates: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
    """
    Compute coordinate-wise median across all client update weight dictionaries.
    Provides a robust baseline reference for cosine similarity and Euclidean distance.
    """
    if not client_updates:
        return {}

    first_delta = client_updates[0]["delta_weights"]
    median_weights: Dict[str, torch.Tensor] = {}

    for key, base_val in first_delta.items():
        if not base_val.is_floating_point():
            median_weights[key] = base_val.clone()
            continue

        stacked = torch.stack([u["delta_weights"][key].float().cpu() for u in client_updates], dim=0)
        # torch.median returns values and indices
        median_val, _ = torch.median(stacked, dim=0)
        median_weights[key] = median_val

    return median_weights

def apply_simulated_attack(
    delta_weights: Dict[str, torch.Tensor],
    attack_type: str,
    severity: float = 1.0
) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
    """
    Simulate malicious attacks on client model weight updates (Section 30).
    Attack Types:
      - 'sign_flipping': delta = -gamma * delta (inverts gradient direction)
      - 'gaussian_noise': delta = delta + N(0, sigma^2) (destroys convergence)
      - 'scaling': delta = beta * delta (extreme scale to dominate aggregation)
      - 'free_rider': delta = 0 (client sends empty gradient without work)
    """
    poisoned: Dict[str, torch.Tensor] = {}
    metadata: Dict[str, Any] = {"attack_type": attack_type, "severity": severity}

    for key, val in delta_weights.items():
        if not val.is_floating_point():
            poisoned[key] = val.clone()
            continue

        p_tensor = val.clone().float()

        if attack_type == "sign_flipping":
            gamma = 1.5 * severity
            p_tensor = -gamma * p_tensor
            metadata["description"] = f"Inverted weight gradients with scaling factor gamma={gamma:.1f}"

        elif attack_type == "gaussian_noise":
            sigma = 0.5 * severity
            noise = torch.randn_like(p_tensor) * sigma
            p_tensor = p_tensor + noise
            metadata["description"] = f"Injected zero-mean Gaussian noise with sigma={sigma:.2f}"

        elif attack_type == "scaling":
            beta = 10.0 * severity
            p_tensor = beta * p_tensor
            metadata["description"] = f"Exaggerated update magnitudes by scaling factor beta={beta:.1f}"

        elif attack_type == "free_rider":
            p_tensor = torch.zeros_like(p_tensor)
            metadata["description"] = "Free-rider attack: zero parameter delta transmitted"

        else:
            p_tensor = val.clone()
            metadata["description"] = "No attack applied (clean update)"

        poisoned[key] = p_tensor

    return poisoned, metadata

def verify_and_score_updates(
    client_updates: List[Dict[str, Any]],
    norm_threshold: float = 5.0,
    cos_threshold: float = -0.1,
    anomaly_threshold: float = 0.55
) -> List[Dict[str, Any]]:
    """
    Mathematical Update Verification Pipeline (Section 30):
      1. Update Norm Bounds: ||Delta W_k||_2 <= tau_norm
      2. Directional Cosine Similarity with Median: cos(Delta W_k, Delta W_med) >= tau_cos
      3. Distance to Median: d_k = ||Delta W_k - Delta W_med||_2
      4. Composite Anomaly Score:
         alpha_k = 0.35 * (norm / tau_norm) + 0.40 * (1 - sim) / 2 + 0.25 * (d_k / max_d)
      5. Action: REJECT if alpha_k > anomaly_threshold or sim < cos_threshold or norm > norm_threshold * 1.5
    """
    if not client_updates:
        return []

    # 1. Compute coordinate median update
    median_delta = compute_coordinate_median_weights(client_updates)
    flat_median = flatten_weights_dict(median_delta)
    median_norm = torch.norm(flat_median, p=2).item()

    flattened_updates = [flatten_weights_dict(u["delta_weights"]) for u in client_updates]
    norms = [torch.norm(f, p=2).item() for f in flattened_updates]

    # Compute distances to median
    distances = [torch.norm(f - flat_median, p=2).item() for f in flattened_updates]
    max_distance = max(distances) if max(distances) > 1e-6 else 1.0

    # Compute cosine similarities
    similarities = []
    for f, n in zip(flattened_updates, norms):
        if n < 1e-7 or median_norm < 1e-7:
            similarities.append(1.0)
        else:
            sim = torch.dot(f, flat_median).item() / (n * median_norm)
            similarities.append(float(np.clip(sim, -1.0, 1.0)))

    # Compute composite anomaly score and determine actions
    verified_updates = []
    for i, u in enumerate(client_updates):
        norm_val = norms[i]
        sim_val = similarities[i]
        dist_val = distances[i]

        norm_factor = min(2.0, norm_val / norm_threshold)
        sim_factor = (1.0 - sim_val) / 2.0  # Normalized to [0, 1]
        dist_factor = dist_val / max_distance

        composite_anomaly = 0.35 * min(1.0, norm_factor) + 0.40 * sim_factor + 0.25 * dist_factor
        composite_anomaly = round(float(np.clip(composite_anomaly, 0.0, 1.0)), 4)

        # Decision rules
        is_rejected = False
        rejection_reason = None
        action = "ACCEPTED"

        if sim_val < cos_threshold:
            is_rejected = True
            rejection_reason = f"Sign-inversion or divergent direction detected (cosine similarity {sim_val:.3f} < {cos_threshold})"
            action = "REJECTED"
        elif norm_val > norm_threshold * 1.5:
            is_rejected = True
            rejection_reason = f"Update magnitude exceeded safety ceiling (norm {norm_val:.2f} > {norm_threshold * 1.5:.2f})"
            action = "REJECTED"
        elif composite_anomaly > anomaly_threshold:
            is_rejected = True
            rejection_reason = f"Composite anomaly score ({composite_anomaly:.3f}) exceeded threshold ({anomaly_threshold})"
            action = "REJECTED"
        elif composite_anomaly > 0.40:
            action = "DOWN_WEIGHTED"

        verified = dict(u)
        verified["update_norm"] = round(norm_val, 4)
        verified["cosine_similarity"] = round(sim_val, 4)
        verified["distance_to_median"] = round(dist_val, 4)
        verified["anomaly_score"] = composite_anomaly
        verified["is_rejected"] = is_rejected
        verified["rejection_reason"] = rejection_reason
        verified["security_action"] = action
        verified_updates.append(verified)

    return verified_updates
