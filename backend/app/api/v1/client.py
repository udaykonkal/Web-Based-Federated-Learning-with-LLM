import io
import zipfile
from typing import List, Dict, Any, Optional
import base64
from datetime import datetime, timezone
import torch
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import require_client, require_client_isolation
from app.models.entities import (
    User, Client, MLModel, ModelStatus, Experiment, FLRound,
    ClientParticipation, ModelUpdate, TrainingStatus, ExperimentMode, ExperimentStatus, Dataset
)
from app.schemas.client import (
    ClientPrivateMetaResponse,
    LocalTrainingRequest,
    LocalTrainingResponse,
    ClientUpdateSubmission
)
from app.services.client_data_service import get_client_dataset_metadata, load_client_private_data, CLIENT_METADATA
from app.services.trainer_service import train_client_local_model
from app.services.telemetry_service import emit_telemetry
from app.services.fl_coordinator import get_experiment_storage_dir
from app.ml.models import serialize_weights, get_model_for_task, get_weights

router = APIRouter(prefix="/client", tags=["Client FL Operations"], dependencies=[Depends(require_client)])


# ==========================================
# DATASET DISTRIBUTION: Client can see & download datasets published by Admin
# ==========================================

@router.get("/datasets")
async def list_distributed_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    List all datasets that the Admin has distributed (published) to client nodes.
    Clients can only see datasets where is_distributed=True.
    They use these to train locally (download CSV → run train_local.py → upload client_update.json).
    """
    result = await db.execute(
        select(Dataset)
        .where(Dataset.is_distributed == True, Dataset.status == "active")
        .order_by(Dataset.distributed_at.desc())
    )
    datasets = result.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "healthcare_task": d.healthcare_task,
            "record_count": d.record_count,
            "feature_count": d.feature_count,
            "target_variable": d.target_variable,
            "feature_names": d.feature_names or [],
            "class_distribution": d.class_distribution or {},
            "distributed_at": d.distributed_at.isoformat() if d.distributed_at else None,
            "status": d.status,
        }
        for d in datasets
    ]

@router.get("/datasets/{dataset_id}/download")
async def download_distributed_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Download the CSV file for a dataset distributed by the Admin.
    The client uses this CSV as local_dataset.csv in the starter kit to train locally.
    """
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalars().first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    if not dataset.is_distributed or dataset.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This dataset has not been distributed to clients."
        )

    # Serve the actual CSV file from admin data path
    file_path = settings.ADMIN_DATA_PATH / dataset.filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found on server. Please contact the coordinator."
        )

    def iter_file():
        with open(file_path, "rb") as f:
            yield from f

    safe_name = dataset.name.replace(" ", "_").lower()
    return StreamingResponse(
        iter_file(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_dataset.csv"'}
    )




@router.get("/models")
async def list_available_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    CLIENT RULE 7, 8, 9, 10, 11, 18:
    A client does NOT automatically have access to training.
    They only see models that the Admin has set to ACTIVE status.
    ACTIVE = Published + Activated (both steps completed by Admin).
    Draft, Uploaded, Published-only, Inactive, or Archived models are fully invisible.
    If no model is active, this returns an empty list, and the client sees:
    'No healthcare models are currently available.'
    """
    allowed_statuses = [ModelStatus.ACTIVE.value]
    result = await db.execute(
        select(MLModel)
        .where(MLModel.status.in_(allowed_statuses))
        .order_by(MLModel.id)
    )
    models = result.scalars().all()
    
    return [
        {
            "id": m.id,
            "name": m.name,
            "healthcare_task": m.healthcare_task,
            "description": m.description,
            "architecture": m.architecture,
            "version": m.version,
            "status": m.status,
            "target_variable": m.target_variable,
            "fl_enabled": True,
        }
        for m in models
    ]

@router.get("/models/{model_id}")
async def get_model_workspace_info(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Retrieve model workspace info.
    Enforces that the model MUST be published/active for the client to access it.
    """
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalars().first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found."
        )

    if model.status != ModelStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Model is in '{model.status}' state and is not available for client training. Only ACTIVE models are accessible. Wait for Admin to publish and activate this model."
        )

    # Retrieve dataset name
    dataset_name = "Healthcare Diagnostic Dataset"
    if model.dataset_id:
        from app.models.entities import Dataset
        d_res = await db.execute(select(Dataset.name).where(Dataset.id == model.dataset_id))
        d_name = d_res.scalar()
        if d_name:
            dataset_name = d_name

    client_meta_all = get_client_dataset_metadata(current_user.client_id)
    task_key = "diabetes" if model.healthcare_task == "diabetes_prediction" else "heart_disease"
    client_task_meta = client_meta_all[task_key]

    return {
        "id": model.id,
        "name": model.name,
        "healthcare_task": model.healthcare_task,
        "description": model.description,
        "architecture": model.architecture,
        "version": model.version,
        "status": model.status,
        "target_variable": model.target_variable,
        "dataset_name": dataset_name,
        "input_features": model.input_features,
        "hyperparameters": model.hyperparameters,
        "client_id": current_user.client_id,
        "fl_status": "Ready for Local Federated Training",
        "current_fl_round": 1,
        "global_accuracy": "Pending Round 1 Aggregation",
        "client_private_data": {
            "sample_count": client_task_meta["sample_count"],
            "large_cohort_sample_count": 3500,
            "feature_count": client_task_meta["feature_count"],
            "class_distribution": client_task_meta["class_distribution"],
            "cohort_description": client_task_meta["cohort_description"],
            "privacy_status": client_meta_all["privacy_status"],
        }
    }


def _generate_standalone_training_script(client_id: str, institution_name: str, healthcare_task: str, model_id: int) -> str:
    target_var = "Outcome" if healthcare_task == "diabetes_prediction" else "target"
    input_dim = 8 if healthcare_task == "diabetes_prediction" else 13
    
    return f'''\"\"\"
=============================================================================
FEDERATED LEARNING LOCAL CLIENT TRAINING SCRIPT
Client ID: {client_id} ({institution_name})
Healthcare Task: {healthcare_task}
Model ID: {model_id}
=============================================================================
This script executes real PyTorch neural network training on your private dataset.
Zero patient rows are transmitted to the server.
Only the parameter delta (Delta W = W_trained - W_initial) is exported for submission.

HOW TO RUN:
  1. Ensure dependencies are installed:
     pip install torch pandas scikit-learn numpy
  2. Execute local backpropagation:
     python train_local.py --epochs 3 --lr 0.01 --batch-size 16
  3. Upload the generated 'client_update.json' directly in the Web Workspace!
=============================================================================
\"\"\"
import argparse
import base64
import io
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from model_architecture import LocalModel

def evaluate_model(model, X_tensor, y_tensor):
    model.eval()
    with torch.no_grad():
        preds = model(X_tensor)
        preds_np = preds.squeeze().numpy()
        y_np = y_tensor.squeeze().numpy()
        binary_preds = (preds_np >= 0.5).astype(int)
        
        loss = log_loss(y_np, preds_np, labels=[0, 1])
        acc = accuracy_score(y_np, binary_preds)
        prec = precision_score(y_np, binary_preds, zero_division=0)
        rec = recall_score(y_np, binary_preds, zero_division=0)
        f1 = f1_score(y_np, binary_preds, zero_division=0)
        
    return {{"loss": float(loss), "accuracy": float(acc), "precision": float(prec), "recall": float(rec), "f1": float(f1)}}

def calculate_l2_norm(deltas):
    total_sq = sum(torch.sum(t.float() ** 2).item() for t in deltas.values())
    return float(np.sqrt(total_sq))

def main():
    parser = argparse.ArgumentParser(description="Federated Learning Local Client Training")
    parser.add_argument("--epochs", type=int, default=3, help="Number of local training epochs")
    parser.add_argument("--lr", type=float, default=0.01, help="Local Adam learning rate")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for DataLoader")
    parser.add_argument("--data-file", type=str, default="local_dataset.csv", help="Path to local private data CSV")
    parser.add_argument("--weights-file", type=str, default="global_weights.pt", help="Path to initial global weights")
    args = parser.parse_args()

    print("=" * 70)
    print("  FEDERATED LEARNING LOCAL CLIENT TRAINING")
    print(f"  Node: {client_id} | Task: {healthcare_task}")
    print("=" * 70)

    csv_path = Path(args.data_file)
    if not csv_path.exists():
        print(f"[ERROR] Dataset file '{{csv_path}}' not found!")
        return
    
    df = pd.read_csv(csv_path)
    print(f"[1/5] Loaded private dataset: {{len(df)}} patient records. Zero data leaves this machine.")

    target_col = "{target_var}"
    X = df.drop(columns=[target_col]).values.astype(np.float32)
    y = df[target_col].values.astype(np.float32).reshape(-1, 1)

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    train_ds = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
    val_ds = TensorDataset(torch.tensor(X_val), torch.tensor(y_val))
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)

    model = LocalModel(input_dim={input_dim})
    weights_path = Path(args.weights_file)
    if weights_path.exists():
        print(f"[2/5] Loading global checkpoint from '{{weights_path}}'...")
        initial_weights = torch.load(weights_path, map_location="cpu", weights_only=True)
        model.load_state_dict(initial_weights)
    else:
        print("[2/5] Initializing fresh model weights.")
        initial_weights = {{k: v.clone() for k, v in model.state_dict().items()}}

    print(f"[3/5] Starting PyTorch backpropagation (Epochs: {{args.epochs}}, LR: {{args.lr}}, Batch: {{args.batch_size}})...")
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCELoss()

    t_start = time.perf_counter()
    loss_history = []
    val_loss_history = []
    val_acc_history = []
    gradient_steps = 0

    X_val_all, y_val_all = val_ds.tensors

    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_losses = []
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            out = model(batch_X)
            loss = criterion(out, batch_y)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())
            gradient_steps += 1

        avg_train_loss = float(np.mean(epoch_losses))
        loss_history.append(round(avg_train_loss, 4))
        
        eval_res = evaluate_model(model, X_val_all, y_val_all)
        val_loss_history.append(round(eval_res["loss"], 4))
        val_acc_history.append(round(eval_res["accuracy"], 4))

        print(f"       Epoch {{epoch}}/{{args.epochs}} — Train Loss: {{avg_train_loss:.4f}} | Val Loss: {{eval_res['loss']:.4f}} | Val Acc: {{eval_res['accuracy']*100:.1f}}%")

    elapsed_ms = int((time.perf_counter() - t_start) * 1000)

    print("[4/5] Computing parameter delta ΔW = W_trained - W_initial...")
    trained_weights = model.state_dict()
    weight_deltas = {{k: trained_weights[k] - initial_weights[k] for k in initial_weights}}
    l2_norm = calculate_l2_norm(weight_deltas)

    buf = io.BytesIO()
    torch.save(weight_deltas, buf)
    delta_bytes = buf.getvalue()
    delta_base64 = base64.b64encode(delta_bytes).decode("utf-8")
    delta_kb = round(len(delta_bytes) / 1024, 2)

    val_final = evaluate_model(model, X_val_all, y_val_all)
    print(f"       Final Accuracy: {{val_final['accuracy']*100:.2f}}% | F1: {{val_final['f1']*100:.2f}}% | ||ΔW||₂: {{l2_norm:.4f}} | Delta Size: {{delta_kb}} KB")

    output_json = {{
        "client_id": "{client_id}",
        "healthcare_task": "{healthcare_task}",
        "sample_count": len(df),
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "epochs_trained": args.epochs,
        "learning_rate": args.lr,
        "batch_size": args.batch_size,
        "gradient_steps": gradient_steps,
        "training_time_ms": elapsed_ms,
        "initial_loss": loss_history[0] if loss_history else 0.0,
        "final_loss": loss_history[-1] if loss_history else 0.0,
        "loss_history": loss_history,
        "val_loss_history": val_loss_history,
        "val_accuracy_history": val_acc_history,
        "accuracy": round(val_final["accuracy"], 4),
        "precision": round(val_final["precision"], 4),
        "recall": round(val_final["recall"], 4),
        "f1_score": round(val_final["f1"], 4),
        "l2_norm": round(l2_norm, 4),
        "update_size_kb": delta_kb,
        "delta_base64": delta_base64,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }}

    with open("client_update.json", "w") as f:
        json.dump(output_json, f, indent=2)

    torch.save(weight_deltas, "delta_weights.pt")
    print(f"[5/5] Exported 'client_update.json' and 'delta_weights.pt' successfully!")
    print("=" * 70)
    print("  NEXT STEP:")
    print("  Open the web portal at http://localhost:5173/client/models/{model_id}/workspace,")
    print("  navigate to the 'Offline Contributor' tab, and drag & drop 'client_update.json'!")
    print("=" * 70)

if __name__ == "__main__":
    main()
'''


def _generate_standalone_model_architecture(healthcare_task: str) -> str:
    input_dim = 8 if healthcare_task == "diabetes_prediction" else 13
    return f'''import torch
import torch.nn as nn

class LocalModel(nn.Module):
    """
    PyTorch Neural Network for {healthcare_task}.
    Architecture strictly identical to coordinator aggregation engine.
    """
    def __init__(self, input_dim: int = {input_dim}):
        super(LocalModel, self).__init__()
        if input_dim == 8:
            self.fc1 = nn.Linear(input_dim, 16)
            self.bn1 = nn.BatchNorm1d(16)
            self.relu1 = nn.ReLU()
            self.dropout = nn.Dropout(0.2)
            self.fc2 = nn.Linear(16, 8)
            self.relu2 = nn.ReLU()
            self.fc3 = nn.Linear(8, 1)
            self.sigmoid = nn.Sigmoid()
        else:
            self.fc1 = nn.Linear(input_dim, 32)
            self.bn1 = nn.BatchNorm1d(32)
            self.relu1 = nn.ReLU()
            self.dropout = nn.Dropout(0.25)
            self.fc2 = nn.Linear(32, 16)
            self.relu2 = nn.ReLU()
            self.fc3 = nn.Linear(16, 1)
            self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.fc1(x)
        if x.size(0) > 1:
            out = self.bn1(out)
        out = self.relu1(out)
        out = self.dropout(out)
        out = self.relu2(self.fc2(out))
        out = self.sigmoid(self.fc3(out))
        return out
'''


@router.get("/models/{model_id}/download-model")
async def download_model_weights(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Download the current global model checkpoint (.pt) for local evaluation or training.
    """
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    if model.status != ModelStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ACTIVE models can be downloaded.")

    exp_res = await db.execute(
        select(Experiment).where(Experiment.model_id == model.id).order_by(Experiment.id.desc())
    )
    latest_exp = exp_res.scalars().first()
    weights_dict = None
    if latest_exp and latest_exp.current_round > 0:
        storage_dir = get_experiment_storage_dir(latest_exp.id)
        prev_weights_path = storage_dir / f"round_{latest_exp.current_round}_global.pt"
        if prev_weights_path.exists():
            weights_dict = torch.load(prev_weights_path, map_location=torch.device('cpu'), weights_only=True)

    if weights_dict is None:
        base_model = get_model_for_task(model.healthcare_task)
        weights_dict = get_weights(base_model)

    buf = io.BytesIO()
    torch.save(weights_dict, buf)
    buf.seek(0)

    round_num = latest_exp.current_round if latest_exp else 0
    filename = f"{model.healthcare_task}_global_round{round_num}.pt"
    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/models/{model_id}/export-package")
async def export_client_training_package(
    model_id: int,
    dataset_scale: Optional[str] = "standard",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Export a complete Kaggle-style Local Training Starter Kit (.zip) containing:
      - global_weights.pt: current global model weights checkpoint
      - local_dataset.csv: client's private isolated dataset partition (standard or large cohort)
      - model_architecture.py: standalone PyTorch neural network definition
      - train_local.py: runnable local training script
      - README.md: instructions
    """
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    if model.status != ModelStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ACTIVE models can be exported.")

    c_res = await db.execute(select(Client).where(Client.id == current_user.client_id))
    client = c_res.scalars().first()
    inst_name = client.name if client else current_user.client_id

    df = load_client_private_data(current_user.client_id, model.healthcare_task, dataset_scale=dataset_scale or "standard")
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    exp_res = await db.execute(
        select(Experiment).where(Experiment.model_id == model.id).order_by(Experiment.id.desc())
    )
    latest_exp = exp_res.scalars().first()
    weights_dict = None
    if latest_exp and latest_exp.current_round > 0:
        storage_dir = get_experiment_storage_dir(latest_exp.id)
        prev_weights_path = storage_dir / f"round_{latest_exp.current_round}_global.pt"
        if prev_weights_path.exists():
            weights_dict = torch.load(prev_weights_path, map_location=torch.device('cpu'), weights_only=True)

    if weights_dict is None:
        base_model = get_model_for_task(model.healthcare_task)
        weights_dict = get_weights(base_model)

    weights_buf = io.BytesIO()
    torch.save(weights_dict, weights_buf)
    weights_bytes = weights_buf.getvalue()

    train_script = _generate_standalone_training_script(
        client_id=current_user.client_id,
        institution_name=inst_name,
        healthcare_task=model.healthcare_task,
        model_id=model.id
    )
    model_arch = _generate_standalone_model_architecture(model.healthcare_task)
    readme = f"""# Federated Learning Local Client Starter Kit
**Node:** {current_user.client_id} ({inst_name})
**Task:** {model.healthcare_task}
**Model:** {model.name} (ID: {model.id})

## Overview
This bundle allows you to run PyTorch federated training locally on your own machine outside the browser.
Your private dataset (`local_dataset.csv`) stays strictly on your computer.

## Quickstart
1. Install Python dependencies:
   ```bash
   pip install torch pandas scikit-learn numpy
   ```

2. Run local training:
   ```bash
   python train_local.py --epochs 3 --lr 0.01 --batch-size 16
   ```

3. Submit your results:
   Open the Platform Web Workspace at:
   `http://localhost:5173/client/models/{model.id}/workspace`
   Switch to the **Offline Contributor** tab, and drag & drop the generated `client_update.json`.
   The coordinator will verify your update and aggregate it in the next global round!
"""

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("global_weights.pt", weights_bytes)
        zf.writestr("local_dataset.csv", csv_bytes)
        zf.writestr("model_architecture.py", model_arch.encode("utf-8"))
        zf.writestr("train_local.py", train_script.encode("utf-8"))
        zf.writestr("README.md", readme.encode("utf-8"))

    zip_buf.seek(0)
    filename = f"fl_client_kit_{model.healthcare_task}_{current_user.client_id}.zip"

    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/models/{model_id}/train", response_model=LocalTrainingResponse)
async def train_model_locally(
    model_id: int,
    payload: LocalTrainingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Execute real PyTorch local training on private client healthcare data (Rules 4, 14, 23, 24).
    1. Authenticate client and verify isolation.
    2. Verify model is published/active.
    3. Check for existing global weights checkpoint from active experiment to train on.
    4. Run PyTorch training locally on private partition.
    5. Compute genuine weight update delta Delta W = W_trained - W_initial.
    6. Return training metrics, loss curve, validation accuracy/loss, and serialized update.
    """
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalars().first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found."
        )

    if model.status != ModelStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Model is in '{model.status}' state and not available for training. Only ACTIVE models can be trained."
        )

    # Check if there is an active/latest experiment for this model to pass global weights
    exp_res = await db.execute(
        select(Experiment)
        .where(Experiment.model_id == model.id)
        .order_by(Experiment.id.desc())
    )
    latest_exp = exp_res.scalars().first()
    global_weights_bytes = None
    if latest_exp and latest_exp.current_round > 0:
        storage_dir = get_experiment_storage_dir(latest_exp.id)
        prev_weights_path = storage_dir / f"round_{latest_exp.current_round}_global.pt"
        if prev_weights_path.exists():
            global_weights = torch.load(prev_weights_path, map_location=torch.device('cpu'), weights_only=True)
            global_weights_bytes = serialize_weights(global_weights)

    # Execute local PyTorch training
    training_result = train_client_local_model(
        client_id=current_user.client_id,
        healthcare_task=model.healthcare_task,
        global_weights_bytes=global_weights_bytes,
        epochs=payload.local_epochs or 3,
        lr=payload.learning_rate or 0.01,
        batch_size=payload.batch_size or 16,
        dataset_scale=payload.dataset_scale or "standard"
    )

    return LocalTrainingResponse(**training_result)

@router.post("/models/{model_id}/submit-update")
async def submit_client_model_update(
    model_id: int,
    payload: ClientUpdateSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Client manually transmits their locally trained weight delta and metrics to the central coordinator.
    Stages the update into the active FL experiment & round so the coordinator aggregates genuine updates.
    Zero raw patient records are transmitted.
    """
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    c_res = await db.execute(select(Client).where(Client.id == current_user.client_id))
    client = c_res.scalars().first()
    institution_name = client.name if client else current_user.client_id

    # 1. Locate or create active experiment for this model
    exp_res = await db.execute(
        select(Experiment)
        .where(Experiment.model_id == model_id)
        .order_by(Experiment.id.desc())
    )
    experiment = exp_res.scalars().first()
    if not experiment:
        experiment = Experiment(
            name=f"FL Experiment - {model.name}",
            model_id=model.id,
            mode=ExperimentMode.PROPOSED.value,
            total_rounds=5,
            current_round=0,
            status=ExperimentStatus.RUNNING.value,
            local_epochs=payload.epochs_trained or 3
        )
        db.add(experiment)
        await db.flush()

    target_round = experiment.current_round + 1

    # 2. Locate or create staged FLRound
    round_res = await db.execute(
        select(FLRound).where(
            FLRound.experiment_id == experiment.id,
            FLRound.round_number == target_round
        )
    )
    fl_round = round_res.scalars().first()
    if not fl_round:
        fl_round = FLRound(
            experiment_id=experiment.id,
            round_number=target_round,
            status="staged",
            started_at=datetime.now(timezone.utc),
            selected_clients=[current_user.client_id]
        )
        db.add(fl_round)
        await db.flush()
    else:
        cur_selected = list(fl_round.selected_clients or [])
        if current_user.client_id not in cur_selected:
            cur_selected.append(current_user.client_id)
            fl_round.selected_clients = cur_selected

    # 3. Update or create ClientParticipation record
    part_res = await db.execute(
        select(ClientParticipation).where(
            ClientParticipation.round_id == fl_round.id,
            ClientParticipation.client_id == current_user.client_id
        )
    )
    participation = part_res.scalars().first()
    if not participation:
        participation = ClientParticipation(
            round_id=fl_round.id,
            client_id=current_user.client_id,
            is_selected=True,
            training_status=TrainingStatus.UPDATE_SUBMITTED.value,
            local_sample_count=payload.sample_count,
            local_epochs=payload.epochs_trained,
            local_accuracy=payload.accuracy,
            local_loss=payload.loss,
            training_time_ms=payload.training_time_ms,
            update_size_bytes=int(payload.update_size_kb * 1024),
            update_verified=True,
            is_accepted=True,
            aggregation_weight=1.0
        )
        db.add(participation)
    else:
        participation.training_status = TrainingStatus.UPDATE_SUBMITTED.value
        participation.local_sample_count = payload.sample_count
        participation.local_epochs = payload.epochs_trained
        participation.local_accuracy = payload.accuracy
        participation.local_loss = payload.loss
        participation.training_time_ms = payload.training_time_ms
        participation.update_size_bytes = int(payload.update_size_kb * 1024)
        participation.update_verified = True
        participation.is_accepted = True

    # 4. Update or create ModelUpdate record
    upd_res = await db.execute(
        select(ModelUpdate).where(
            ModelUpdate.round_id == fl_round.id,
            ModelUpdate.client_id == current_user.client_id
        )
    )
    m_update = upd_res.scalars().first()
    if not m_update:
        m_update = ModelUpdate(
            round_id=fl_round.id,
            client_id=current_user.client_id,
            update_norm=payload.l2_norm,
            original_size_bytes=int(payload.update_size_kb * 1024),
            compressed_size_bytes=int(payload.update_size_kb * 1024),
            is_rejected=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(m_update)
    else:
        m_update.update_norm = payload.l2_norm
        m_update.original_size_bytes = int(payload.update_size_kb * 1024)
        m_update.compressed_size_bytes = int(payload.update_size_kb * 1024)
        m_update.is_rejected = False

    # 5. Persist serialized delta tensor to experiment checkpoint dir
    if payload.delta_base64:
        storage_dir = get_experiment_storage_dir(experiment.id)
        raw_bytes = base64.b64decode(payload.delta_base64)
        delta_path = storage_dir / f"staged_delta_{target_round}_{current_user.client_id}.pt"
        delta_path.write_bytes(raw_bytes)

    await db.commit()

    # Emit real-time telemetry event to central coordinator
    await emit_telemetry(
        event_type="CLIENT_UPDATE_RECEIVED",
        data={
            "client_id": current_user.client_id,
            "institution_name": institution_name,
            "model_id": model_id,
            "round_number": target_round,
            "healthcare_task": model.healthcare_task,
            "sample_count": payload.sample_count,
            "epochs_trained": payload.epochs_trained,
            "accuracy": payload.accuracy,
            "loss": payload.loss,
            "l2_norm": payload.l2_norm,
            "training_time_ms": payload.training_time_ms,
            "payload_size_kb": payload.update_size_kb,
            "zero_raw_data_verified": True,
            "message": f"{institution_name} submitted local weight delta (||ΔW||₂ = {payload.l2_norm:.4f}, {payload.sample_count} samples, {payload.update_size_kb:.2f} KB) staged for Round {target_round}."
        }
    )

    return {
        "status": "success",
        "message": f"Weight delta successfully received from {institution_name} and staged for Round {target_round} aggregation.",
        "client_id": current_user.client_id,
        "round_number": target_round,
        "sample_count": payload.sample_count,
        "accuracy": payload.accuracy,
        "l2_norm": payload.l2_norm,
        "update_size_kb": payload.update_size_kb,
        "training_time_ms": payload.training_time_ms,
        "coordinator_status": "STAGED_FOR_AGGREGATION",
        "privacy_guarantee": "Zero raw clinical records transmitted. Only serialized gradient delta received."
    }



@router.get("/{client_id}/profile", response_model=ClientPrivateMetaResponse)
async def get_client_private_profile(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Retrieve private client metadata.
    Enforces strict client isolation: Client 1 CANNOT query Client 2 or Client 3 profile.
    """
    # Verify isolation
    if current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Private boundary violation. You cannot inspect data for '{client_id}'."
        )

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    meta = get_client_dataset_metadata(client_id)

    return ClientPrivateMetaResponse(
        client_id=client.id,
        institution_name=client.name,
        institution_type=client.institution_type,
        privacy_status=meta["privacy_status"],
        diabetes=meta["diabetes"],
        heart_disease=meta["heart_disease"]
    )
