import base64
from typing import Dict, Any, List, Optional, Tuple
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from app.services.client_data_service import load_client_private_data
from app.ml.models import (
    get_model_for_task,
    get_weights,
    set_weights,
    compute_weight_delta,
    calculate_l2_norm,
    serialize_weights,
    deserialize_weights,
    evaluate_model
)

def prepare_client_tensors(
    df: pd.DataFrame,
    target_variable: str,
    val_split: float = 0.2,
    random_state: int = 42
) -> Tuple[TensorDataset, TensorDataset, StandardScaler]:
    """
    Split private client data into standardized train and validation tensor datasets.
    Zero raw patient records leave this local execution scope.
    """
    X = df.drop(columns=[target_variable]).values.astype(np.float32)
    y = df[target_variable].values.astype(np.float32).reshape(-1, 1)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=val_split, random_state=random_state, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    train_ds = TensorDataset(torch.tensor(X_train_scaled), torch.tensor(y_train))
    val_ds = TensorDataset(torch.tensor(X_val_scaled), torch.tensor(y_val))

    return train_ds, val_ds, scaler

def train_client_local_model(
    client_id: str,
    healthcare_task: str,
    global_weights_bytes: Optional[bytes] = None,
    epochs: int = 3,
    lr: float = 0.01,
    batch_size: int = 16,
    dataset_scale: str = "standard"
) -> Dict[str, Any]:
    """
    Execute real PyTorch neural network training on private institutional healthcare data.
    Strictly adheres to Rule 4, 23 & 24:
      1. Receives current global model weights (or initializes if Round 1).
      2. Trains local model on private patient data for E epochs.
      3. Computes genuine parameter delta: Delta W = W_local - W_global.
      4. Measures real loss, accuracy, precision, recall, F1, and delta L2 norm.
    """
    # 1. Load private dataset (standard isolated shard or large clinical cohort)
    df = load_client_private_data(client_id, healthcare_task, dataset_scale=dataset_scale)
    target_var = "Outcome" if healthcare_task == "diabetes_prediction" else "target"

    train_ds, val_ds, scaler = prepare_client_tensors(df, target_var)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    # 2. Instantiate PyTorch Neural Network
    model = get_model_for_task(healthcare_task)

    if global_weights_bytes:
        global_weights = deserialize_weights(global_weights_bytes)
        set_weights(model, global_weights)

    # Record initial weights before local gradient steps
    initial_weights = get_weights(model)

    import time
    t_start = time.perf_counter()

    # 3. Setup optimizer and loss function
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    # 4. Local Training Loop across E epochs
    loss_history = []
    val_loss_history = []
    val_accuracy_history = []
    gradient_steps = 0

    X_val_all, y_val_all = val_ds.tensors

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_losses = []
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())
            gradient_steps += 1

        avg_loss = float(np.mean(epoch_losses))
        loss_history.append(round(avg_loss, 4))

        # Evaluate validation metrics at end of this epoch
        epoch_val = evaluate_model(model, X_val_all, y_val_all)
        val_loss_history.append(epoch_val["loss"])
        val_accuracy_history.append(epoch_val["accuracy"])

    # 5. Extract trained weights and compute genuine parameter delta Delta W
    trained_weights = get_weights(model)
    weight_deltas = compute_weight_delta(initial_weights, trained_weights)
    l2_norm = calculate_l2_norm(weight_deltas)

    # 6. Final evaluation of local validation performance
    val_metrics = evaluate_model(model, X_val_all, y_val_all)

    # 7. Serialize weight delta update
    serialized_delta = serialize_weights(weight_deltas)
    delta_base64 = base64.b64encode(serialized_delta).decode('utf-8')
    update_size_kb = round(len(serialized_delta) / 1024, 2)
    training_time_ms = max(1, int((time.perf_counter() - t_start) * 1000))

    return {
        "client_id": client_id,
        "healthcare_task": healthcare_task,
        "dataset_scale": dataset_scale,
        "sample_count": len(df),
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "epochs_trained": epochs,
        "learning_rate": lr,
        "batch_size": batch_size,
        "gradient_steps": gradient_steps,
        "training_time_ms": training_time_ms,
        "initial_loss": loss_history[0] if loss_history else 0.0,
        "final_loss": loss_history[-1] if loss_history else 0.0,
        "loss_history": loss_history,
        "val_loss_history": val_loss_history,
        "val_accuracy_history": val_accuracy_history,
        "accuracy": val_metrics["accuracy"],
        "precision": val_metrics["precision"],
        "recall": val_metrics["recall"],
        "f1_score": val_metrics["f1_score"],
        "l2_norm": round(l2_norm, 6),
        "update_size_kb": update_size_kb,
        "delta_base64": delta_base64,  # Serialized parameter delta for transmission to server
        "timestamp": pd.Timestamp.now().isoformat()
    }

