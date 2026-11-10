"""
=============================================================================
CODE 2: ADVERSARIAL SIGN-FLIPPING / NEGATIVE VALUES UPDATE SUBMISSION
=============================================================================
This script simulates a Section 30 Adversarial Attack (Sign-Inversion / Negative Gradients):
  - Inverts the genuine local training updates by multiplying by -gamma (negative values).
  - Transmits inverted negative gradients (ΔW_malicious = -1.5 * ΔW_clean) to the Central Server.
  - Triggers the Central Coordinator's Mathematical Anomaly Screening:
      1. Directional Cosine Similarity with Coordinate Median: cos(ΔW, ΔW_med) < -0.10
      2. Composite Anomaly Score Spike
  - Detection Outcome:
      -> Flagged: REJECTED
      -> Reason: "Sign-inversion or divergent direction detected (cosine similarity < -0.1)"
      -> Action: Drop update from FedAvg aggregation to protect global model integrity.
=============================================================================
"""

import io
import time
import base64
import requests
import numpy as np
import torch
import torch.nn as nn

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SERVER_URL = "http://127.0.0.1:8000"
CLIENT_EMAIL = "hospital_c@flplatform.org"  # Compromised Node (Hospital C)
CLIENT_PASSWORD = "client3pass"
ADMIN_EMAIL = "admin@flplatform.org"
ADMIN_PASSWORD = "admin123"
MODEL_ID = 1

print("=" * 75)
print("  SIDE B: COMPROMISED CLIENT (NEGATIVE / SIGN-FLIPPED VALUES ATTACK)")
print("=" * 75)

# ---------------------------------------------------------------------------
# Step 1: Authenticate as Hospital C (Compromised Client)
# ---------------------------------------------------------------------------
print("\n[1/5] Authenticating as Hospital C (Compromised Client Node)...")
auth_res = requests.post(
    f"{SERVER_URL}/api/v1/auth/login",
    json={"email": CLIENT_EMAIL, "password": CLIENT_PASSWORD},
    timeout=10
)
if auth_res.status_code != 200:
    raise RuntimeError(f"Authentication failed: {auth_res.text}")

token_info = auth_res.json()
token = token_info["access_token"]
headers = {"Authorization": f"Bearer {token}"}
client_label = token_info.get("institution_name") or token_info.get("email")
print(f"       -> Authenticated as '{client_label}'")

# ---------------------------------------------------------------------------
# Step 2: Compute Baseline Local Weights
# ---------------------------------------------------------------------------
print("\n[2/5] Initializing local neural network and computing base weight delta...")
class ClientLocalMLP(nn.Module):
    def __init__(self, in_features=8):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)

torch.manual_seed(101)
model = ClientLocalMLP(in_features=8)
initial_weights = {k: v.clone() for k, v in model.state_dict().items()}

# Normal gradient step
X_dummy = torch.randn(155, 8)
y_dummy = (torch.sigmoid(X_dummy[:, 0:1]) > 0.5).float()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
criterion = nn.BCELoss()
optimizer.zero_grad()
loss = criterion(model(X_dummy), y_dummy)
loss.backward()
optimizer.step()

clean_weights = model.state_dict()
clean_delta = {k: (clean_weights[k] - initial_weights[k]) for k in initial_weights}

# ---------------------------------------------------------------------------
# Step 3: Inject Malicious Negative Values (Sign-Flipping Attack)
# ---------------------------------------------------------------------------
print("\n[3/5] Injecting NEGATIVE VALUES / SIGN-FLIPPING attack on parameters...")
gamma = 1.5  # Inversion factor
poisoned_delta = {}

for k, v in clean_delta.items():
    if v.is_floating_point():
        # Invert direction to negative values: dW_attack = -gamma * dW
        poisoned_delta[k] = -gamma * v.clone()
    else:
        poisoned_delta[k] = v.clone()

# Verify that values are inverted into opposite negative direction
clean_sample_val = list(clean_delta.values())[0][0, 0].item()
poisoned_sample_val = list(poisoned_delta.values())[0][0, 0].item()
print(f"       -> Sample Parameter Clean dW   : {clean_sample_val:+.6f}")
print(f"       -> Sample Parameter Poisoned dW: {poisoned_sample_val:+.6f} (SIGN INVERTED)")

total_sq = sum(torch.sum(t.float() ** 2).item() for t in poisoned_delta.values())
l2_norm = float(np.sqrt(total_sq))

buf = io.BytesIO()
torch.save(poisoned_delta, buf)
delta_bytes = buf.getvalue()
delta_base64 = base64.b64encode(delta_bytes).decode("utf-8")
delta_kb = round(len(delta_bytes) / 1024, 2)

# ---------------------------------------------------------------------------
# Step 4: Transmit Negative Values Update to Central Server
# ---------------------------------------------------------------------------
print("\n[4/5] Transmitting inverted negative parameter update to Central Coordinator...")
payload = {
    "sample_count": 155,
    "epochs_trained": 3,
    "accuracy": 0.42,  # Degraded due to inverted parameters
    "loss": 0.89,
    "dice_coefficient": 0.35,
    "l2_norm": round(l2_norm, 4),
    "update_size_kb": delta_kb,
    "training_time_ms": 650,
    "delta_base64": delta_base64
}

stage_res = requests.post(
    f"{SERVER_URL}/api/v1/client/models/{MODEL_ID}/submit-update",
    json=payload,
    headers=headers,
    timeout=10
)
print(f"       -> Staged update to Central Coordinator (HTTP {stage_res.status_code})")

# ---------------------------------------------------------------------------
# Step 5: Screen Update through Central Server Defense Pipeline
# ---------------------------------------------------------------------------
print("\n[5/5] Running Central Coordinator Mathematical Security Screening Engine...")

# Authenticate as Central Admin to query mathematical screening telemetry
admin_login = requests.post(
    f"{SERVER_URL}/api/v1/auth/login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    timeout=10
)
admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

# Trigger real mathematical defense inspection on the attack
defense_res = requests.post(
    f"{SERVER_URL}/api/v1/admin/security/simulate-attack",
    json={
        "client_id": "client_3",
        "attack_type": "sign_flipping",
        "severity": 1.0,
        "task": "diabetes_prediction"
    },
    headers=admin_headers,
    timeout=15
)

defense_data = defense_res.json()
sim_attack = defense_data["simulated_attack"]
screened_nodes = defense_data["all_screened_nodes"]

print("=" * 75)
print("  CENTRAL COORDINATOR DEFENSE DETECTION REPORT:")
print("=" * 75)
print(f"  Targeted Attacker Node : {sim_attack['attacker_client']}")
print(f"  Attack Signature       : {sim_attack['attack_type']} (Negative Values / Gradient Inversion)")
print(f"  Attack Detected by FL  : {sim_attack['detected']}")
print(f"  Central Server Action  : {sim_attack['action_taken']} (Dropped from FedAvg)")
print(f"  Detection Reason       : {sim_attack['rejection_reason']}")
print("-" * 75)
print("  SCREENED NODES COMPARISON TABLE:")
print(f"  {'Client ID':12} | {'Cosine Sim':12} | {'L2 Norm':10} | {'Anomaly Score':14} | {'Action':10}")
print("-" * 75)
for node in screened_nodes:
    print(f"  {node['client_id']:12} | {node['cosine_similarity']:+12.4f} | {node['update_norm']:10.4f} | {node['anomaly_score']:14.4f} | {node['security_action']:10}")
print("=" * 75)
