from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import MLModel, ModelStatus, Dataset
from app.services.dataset_service import HEALTHCARE_SCHEMAS

# Default PyTorch MLP architecture definitions for the two healthcare tasks
DEFAULT_HEALTHCARE_MODELS = [
    {
        "name": "Diabetes Prediction Neural Network",
        "healthcare_task": "diabetes_prediction",
        "description": "Deep Multi-Layer Perceptron (MLP) for binary diabetic diagnostic risk classification. Includes Dropout and BatchNorm.",
        "architecture": "MLP (8 -> 16 -> 8 -> 1)",
        "version": "v1.0",
        "status": ModelStatus.DRAFT.value,  # Starts in DRAFT so Admin has to publish it (Rule 9 & 47)
        "target_variable": "Outcome",
        "input_features": HEALTHCARE_SCHEMAS["diabetes_prediction"]["features"],
        "hyperparameters": {
            "hidden_dims": [16, 8],
            "dropout_rate": 0.2,
            "learning_rate": 0.01,
            "batch_size": 16,
            "local_epochs": 3,
            "optimizer": "Adam",
            "loss_fn": "BCELoss"
        }
    },
    {
        "name": "Heart Disease Risk Classifier",
        "healthcare_task": "heart_disease_prediction",
        "description": "Deep Multi-Layer Perceptron (MLP) for cardiovascular disease presence classification based on clinical parameters.",
        "architecture": "MLP (13 -> 32 -> 16 -> 1)",
        "version": "v1.0",
        "status": ModelStatus.DRAFT.value,  # Starts in DRAFT so Admin has to publish it (Rule 9 & 47)
        "target_variable": "target",
        "input_features": HEALTHCARE_SCHEMAS["heart_disease_prediction"]["features"],
        "hyperparameters": {
            "hidden_dims": [32, 16],
            "dropout_rate": 0.25,
            "learning_rate": 0.005,
            "batch_size": 16,
            "local_epochs": 3,
            "optimizer": "Adam",
            "loss_fn": "BCELoss"
        }
    }
]

VALID_STATUS_TRANSITIONS = {
    ModelStatus.DRAFT.value: [ModelStatus.UPLOADED.value, ModelStatus.PUBLISHED.value, ModelStatus.ARCHIVED.value],
    ModelStatus.UPLOADED.value: [ModelStatus.PUBLISHED.value, ModelStatus.DRAFT.value, ModelStatus.ARCHIVED.value],
    ModelStatus.PUBLISHED.value: [ModelStatus.ACTIVE.value, ModelStatus.INACTIVE.value, ModelStatus.ARCHIVED.value],
    ModelStatus.ACTIVE.value: [ModelStatus.INACTIVE.value, ModelStatus.PUBLISHED.value, ModelStatus.ARCHIVED.value],
    ModelStatus.INACTIVE.value: [ModelStatus.ACTIVE.value, ModelStatus.ARCHIVED.value],
    ModelStatus.ARCHIVED.value: [ModelStatus.DRAFT.value]  # Can restore to draft
}

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate model lifecycle state transition."""
    if current_status == new_status:
        return True
    allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed

async def initialize_default_healthcare_models(db: AsyncSession) -> List[MLModel]:
    """
    Seed initial ML model entities in DRAFT state if not already created.
    This strictly enforces Rule 9 & Rule 47 Stage 1:
    The models exist in the Admin registry as DRAFT, meaning Client still sees 
    'No healthcare models are currently available' until Admin explicitly clicks 'Publish'!
    """
    models = []
    for model_cfg in DEFAULT_HEALTHCARE_MODELS:
        task = model_cfg["healthcare_task"]
        q = await db.execute(select(MLModel).where(MLModel.healthcare_task == task))
        existing = q.scalars().first()

        if not existing:
            # Look up associated dataset
            d_res = await db.execute(select(Dataset).where(Dataset.healthcare_task == task))
            dataset = d_res.scalars().first()

            new_model = MLModel(
                name=model_cfg["name"],
                healthcare_task=task,
                description=model_cfg["description"],
                architecture=model_cfg["architecture"],
                version=model_cfg["version"],
                status=model_cfg["status"],
                dataset_id=dataset.id if dataset else None,
                target_variable=model_cfg["target_variable"],
                input_features=model_cfg["input_features"],
                hyperparameters=model_cfg["hyperparameters"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_model)
            await db.flush()
            models.append(new_model)
        else:
            models.append(existing)

    await db.commit()
    return models
