import io
from typing import Dict, Any, Tuple, Optional
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss

class DiabetesMLP(nn.Module):
    """
    Deep PyTorch Neural Network for Diabetes Risk Classification.
    Architecture: 8 inputs -> 16 hidden -> BatchNorm -> ReLU -> Dropout(0.2) -> 8 hidden -> ReLU -> 1 output -> Sigmoid.
    """
    def __init__(self, input_dim: int = 8):
        super(DiabetesMLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, 16)
        self.bn1 = nn.BatchNorm1d(16)
        self.relu1 = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(16, 8)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(8, 1)
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

class HeartDiseaseMLP(nn.Module):
    """
    Deep PyTorch Neural Network for Heart Disease Risk Classification.
    Architecture: 13 inputs -> 32 hidden -> BatchNorm -> ReLU -> Dropout(0.25) -> 16 hidden -> ReLU -> 1 output -> Sigmoid.
    """
    def __init__(self, input_dim: int = 13):
        super(HeartDiseaseMLP, self).__init__()
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

def get_model_for_task(healthcare_task: str) -> nn.Module:
    """Factory to instantiate the appropriate PyTorch neural network for a healthcare task."""
    if healthcare_task == "diabetes_prediction":
        return DiabetesMLP(input_dim=8)
    elif healthcare_task == "heart_disease_prediction":
        return HeartDiseaseMLP(input_dim=13)
    else:
        raise ValueError(f"Unknown healthcare task '{healthcare_task}'")

def get_weights(model: nn.Module) -> Dict[str, torch.Tensor]:
    """Extract model parameters as a cloned state dictionary of tensors on CPU."""
    return {name: param.detach().cpu().clone() for name, param in model.state_dict().items()}

def set_weights(model: nn.Module, weights: Dict[str, torch.Tensor]):
    """Set model parameters from a state dictionary."""
    model.load_state_dict(weights)

def compute_weight_delta(
    initial_weights: Dict[str, torch.Tensor],
    trained_weights: Dict[str, torch.Tensor]
) -> Dict[str, torch.Tensor]:
    """
    Compute real model update delta:
    Delta W = W_trained - W_initial
    """
    deltas = {}
    for name in initial_weights:
        deltas[name] = trained_weights[name] - initial_weights[name]
    return deltas

def calculate_l2_norm(deltas: Dict[str, torch.Tensor]) -> float:
    """Calculate the global L2 norm of the parameter update tensor dictionary."""
    total_sq = 0.0
    for tensor in deltas.values():
        total_sq += torch.sum(tensor.float() ** 2).item()
    return float(np.sqrt(total_sq))

def serialize_weights(weights: Dict[str, torch.Tensor]) -> bytes:
    """Serialize tensor weights dictionary to bytes."""
    buffer = io.BytesIO()
    torch.save(weights, buffer)
    return buffer.getvalue()

def deserialize_weights(data: bytes) -> Dict[str, torch.Tensor]:
    """Deserialize tensor weights from bytes."""
    buffer = io.BytesIO(data)
    return torch.load(buffer, map_location=torch.device('cpu'), weights_only=True)

def evaluate_model(
    model: nn.Module,
    X_tensor: torch.Tensor,
    y_tensor: torch.Tensor
) -> Dict[str, float]:
    """
    Evaluate PyTorch binary classifier on a test dataset.
    Returns: loss, accuracy, precision, recall, f1_score.
    """
    model.eval()
    criterion = nn.BCELoss()
    with torch.no_grad():
        preds = model(X_tensor)
        loss = criterion(preds, y_tensor).item()
        preds_binary = (preds.squeeze() >= 0.5).long().cpu().numpy()
        y_true = y_tensor.squeeze().long().cpu().numpy()

        acc = float(accuracy_score(y_true, preds_binary))
        prec = float(precision_score(y_true, preds_binary, zero_division=0))
        rec = float(recall_score(y_true, preds_binary, zero_division=0))
        f1 = float(f1_score(y_true, preds_binary, zero_division=0))

    return {
        "loss": round(loss, 4),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4)
    }
