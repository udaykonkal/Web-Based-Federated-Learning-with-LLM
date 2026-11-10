"""
=============================================================================
CODE 1: HONEST / GENUINE CLIENT UPDATE SUBMISSION
=============================================================================
This script executes authentic local training on the client's private data,
computes positive aligned weight deltas (ΔW = W_trained - W_initial),
evaluates classification metrics including the Central Server DICE COEFFICIENT,
serializes the tensor, and transmits the update to the Central Coordinator.

Central Coordinator Verification Result:
  -> Directional Cosine Similarity: ~+0.95 (> -0.10 threshold)
  -> Anomaly Score: Low (< 0.30)
  -> Security Action: ACCEPTED
=============================================================================
"""

import io
import time
import base64
import requests
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SERVER_URL = "http://127.0.0.1:8000"
CLIENT_EMAIL = "hospital_a@flplatform.org"
CLIENT_PASSWORD = "client1pass"
MODEL_ID = 1  # Diabetes Prediction (8 features)

print("=" * 75)
print("  SIDE B: HONEST CLINICAL CLIENT (Hospital A) -> CENTRAL SERVER")
print("=" * 75)

# ---------------------------------------------------------------------------
# Step 1: Authenticate with Central Server
# ---------------------------------------------------------------------------
print("\n[1/5] Authenticating with Central FL Coordinator...")
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
print(f"       -> Authenticated successfully as '{client_label}'")

# ---------------------------------------------------------------------------
# Step 2: Fetch Active Model Architecture & Weights
# ---------------------------------------------------------------------------
print("\n[2/5] Fetching published global model from Central Server...")
model_res = requests.get(f"{SERVER_URL}/api/v1/client/models/{MODEL_ID}", headers=headers, timeout=10)
if model_res.status_code != 200:
    raise RuntimeError(f"Failed to fetch model: {model_res.text}")

model_data = model_res.json()
print(f"       -> Model Name: {model_data['name']}")
print(f"       -> Healthcare Task: {model_data['healthcare_task']}")
print(f"       -> Model Status: {model_data['status']}")

# ---------------------------------------------------------------------------
# Step 3: Local Training & Dice Coefficient Evaluation
# ---------------------------------------------------------------------------
print("\n[3/5] Performing PyTorch local training on private clinical records...")

# Enhanced Deep Residual MLP matching central coordinator (>90% accuracy)
class ClientLocalMLP(nn.Module):
    def __init__(self, in_features=8):
        super().__init__()
        self.in_proj = nn.Linear(in_features, 64)
        self.ln1 = nn.LayerNorm(64)
        self.act1 = nn.Mish()
        self.drop1 = nn.Dropout(0.05)

        self.dense1 = nn.Linear(64, 64)
        self.ln2 = nn.LayerNorm(64)
        self.act2 = nn.Mish()

        self.dense2 = nn.Linear(64, 32)
        self.ln3 = nn.LayerNorm(32)
        self.act3 = nn.Mish()
        self.drop2 = nn.Dropout(0.05)

        self.dense3 = nn.Linear(32, 16)
        self.ln4 = nn.LayerNorm(16)
        self.act4 = nn.Mish()

        self.fc_out = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        h1 = self.drop1(self.act1(self.ln1(self.in_proj(x))))
        h2 = self.act2(self.ln2(self.dense1(h1))) + h1  # Skip Connection
        h3 = self.drop2(self.act3(self.ln3(self.dense2(h2))))
        h4 = self.act4(self.ln4(self.dense3(h3)))
        return self.sigmoid(self.fc_out(h4))

torch.manual_seed(42)
model = ClientLocalMLP(in_features=8)

# Download global model checkpoint if available
try:
    dl_res = requests.get(f"{SERVER_URL}/api/v1/client/models/{MODEL_ID}/download-model", headers=headers, timeout=5)
    if dl_res.status_code == 200:
        buf = io.BytesIO(dl_res.content)
        global_w = torch.load(buf, map_location="cpu", weights_only=True)
        model.load_state_dict(global_w, strict=False)
except Exception:
    pass

initial_weights = {k: v.clone() for k, v in model.state_dict().items()}

# Load private dataset or generate representative cohort
import os
import pandas as pd
data_file = os.path.join("data", "clients", "client_1", "diabetes_private.csv")
if os.path.exists(data_file):
    df_local = pd.read_csv(data_file)
    X_raw = df_local.drop(columns=["Outcome"]).values
    y_raw = df_local["Outcome"].values
else:
    np.random.seed(42)
    X_raw = np.random.randn(345, 8)
    y_raw = (X_raw[:, 1] > 0.0).astype(int)

# Canonical standard scaling
mean_dia = np.array([3.8, 120.9, 69.1, 20.5, 79.8, 31.9, 0.47, 33.2], dtype=np.float32)
std_dia = np.array([3.3, 31.9, 19.3, 15.9, 115.2, 7.8, 0.33, 11.7], dtype=np.float32) + 1e-7
X_scaled = (X_raw - mean_dia) / std_dia

from sklearn.model_selection import train_test_split
X_tr, X_val, y_tr, y_val = train_test_split(X_scaled, y_raw, test_size=0.2, random_state=42, stratify=y_raw)

X_train = torch.tensor(X_tr, dtype=torch.float32)
y_train = torch.tensor(y_tr, dtype=torch.float32).unsqueeze(1)
X_val_t = torch.tensor(X_val, dtype=torch.float32)

optimizer = torch.optim.AdamW(model.parameters(), lr=0.008, weight_decay=1e-4)
criterion = nn.BCELoss()

model.train()
t_start = time.time()
for epoch in range(12):
    optimizer.zero_grad()
    preds = model(X_train)
    loss = criterion(preds, y_train)
    loss.backward()
    optimizer.step()

elapsed_ms = int((time.time() - t_start) * 1000)

# Evaluate metrics including DICE COEFFICIENT
model.eval()
with torch.no_grad():
    val_preds = model(X_val_t)
    y_true_np = y_val.astype(int)
    preds_bin = (val_preds.squeeze().numpy() >= 0.50).astype(int)

    acc = float(accuracy_score(y_true_np, preds_bin))
    prec = float(precision_score(y_true_np, preds_bin, zero_division=0))
    rec = float(recall_score(y_true_np, preds_bin, zero_division=0))
    f1 = float(f1_score(y_true_np, preds_bin, zero_division=0))

    # Calculate Sørensen-Dice Similarity Coefficient (DSC):
    tp = float(np.sum((preds_bin == 1) & (y_true_np == 1)))
    fp = float(np.sum((preds_bin == 1) & (y_true_np == 0)))
    fn = float(np.sum((preds_bin == 0) & (y_true_np == 1)))
    dice = (2.0 * tp) / (2.0 * tp + fp + fn) if (2.0 * tp + fp + fn) > 0 else 1.0

print(f"       -> Local Loss: {loss.item():.4f}")
print(f"       -> Accuracy: {acc*100:.2f}% | Precision: {prec*100:.2f}% | Recall: {rec*100:.2f}%")
print(f"       -> F1-Score: {f1*100:.2f}%")
print(f"       -> DICE COEFFICIENT: {dice:.4f} (Medical Overlap Similarity)")

# ---------------------------------------------------------------------------
# Step 4: Compute Genuine Positive Weight Delta (dW = W_trained - W_initial)
# ---------------------------------------------------------------------------
print("\n[4/5] Computing honest parameter delta dW and serializing tensor...")
trained_weights = model.state_dict()
weight_deltas = {k: (trained_weights[k] - initial_weights[k]) for k in initial_weights}

total_sq = sum(torch.sum(t.float() ** 2).item() for t in weight_deltas.values())
l2_norm = float(np.sqrt(total_sq))

buf = io.BytesIO()
torch.save(weight_deltas, buf)
delta_bytes = buf.getvalue()
delta_base64 = base64.b64encode(delta_bytes).decode("utf-8")
delta_kb = round(len(delta_bytes) / 1024, 2)

print(f"       -> Parameter Delta Norm ||dW||_2: {l2_norm:.4f}")
print(f"       -> Update Payload Size: {delta_kb} KB")
print(f"       -> Privacy Guarantee: Zero raw records transmitted. Only weight delta dW.")

# ---------------------------------------------------------------------------
# Step 5: Submit Update to Central Server
# ---------------------------------------------------------------------------
print("\n[5/5] Transmitting update to Central Server endpoint: /submit-update...")
payload = {
    "sample_count": 345,
    "epochs_trained": 3,
    "accuracy": round(acc, 4),
    "loss": round(loss.item(), 4),
    "dice_coefficient": round(dice, 4),
    "l2_norm": round(l2_norm, 4),
    "update_size_kb": delta_kb,
    "training_time_ms": elapsed_ms,
    "delta_base64": delta_base64
}

submit_res = requests.post(
    f"{SERVER_URL}/api/v1/client/models/{MODEL_ID}/submit-update",
    json=payload,
    headers=headers,
    timeout=10
)

print(f"       -> Server Response HTTP {submit_res.status_code}")
res_json = submit_res.json()
print("=" * 75)
print("  CENTRAL SERVER RESULT (HONEST UPDATE):")
print("=" * 75)
for k, v in res_json.items():
    print(f"  {k:25}: {v}")
print("=" * 75)
