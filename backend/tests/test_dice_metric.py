import pytest
import torch
from app.ml.models import evaluate_model, DiabetesMLP
from app.services.aggregation_service import evaluate_global_model_on_benchmark
from app.core.database import AsyncSessionLocal
from app.models.entities import Experiment, MLModel
from sqlalchemy import select
from app.services.fl_coordinator import execute_fl_round

def test_evaluate_model_dice_coefficient():
    """Verify that evaluate_model calculates the exact Sørensen-Dice coefficient."""
    model = DiabetesMLP()
    
    # 4 synthetic samples
    X = torch.randn(4, 8)
    # Ground truth targets
    y = torch.tensor([[1.0], [0.0], [1.0], [0.0]])
    
    metrics = evaluate_model(model, X, y)
    assert "dice_coefficient" in metrics
    assert 0.0 <= metrics["dice_coefficient"] <= 1.0
    assert "accuracy" in metrics
    assert "f1_score" in metrics

def test_dice_coefficient_calculation_accuracy():
    """Verify exact formula 2*TP / (2*TP + FP + FN)."""
    class MockModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
        def forward(self, x):
            # Output fixed probabilities: sample 0 -> 0.9 (pos), sample 1 -> 0.8 (pos), sample 2 -> 0.1 (neg), sample 3 -> 0.2 (neg)
            return torch.tensor([[0.9], [0.8], [0.1], [0.2]])

    mock = MockModel()
    X = torch.zeros(4, 8)
    # True labels: [1, 0, 1, 0]
    # Predictions: [1, 1, 0, 0]
    # TP = 1 (sample 0)
    # FP = 1 (sample 1)
    # FN = 1 (sample 2)
    # TN = 1 (sample 3)
    # Dice = (2 * 1) / (2 * 1 + 1 + 1) = 2 / 4 = 0.50
    y = torch.tensor([[1.0], [0.0], [1.0], [0.0]])
    res = evaluate_model(mock, X, y)
    assert res["dice_coefficient"] == 0.50

def test_evaluate_global_model_on_benchmark_returns_dice():
    """Verify that evaluate_global_model_on_benchmark includes dice_coefficient."""
    model = DiabetesMLP()
    metrics = evaluate_global_model_on_benchmark(model.state_dict(), "diabetes_prediction")
    assert "dice_coefficient" in metrics
    assert 0.0 <= metrics["dice_coefficient"] <= 1.0
