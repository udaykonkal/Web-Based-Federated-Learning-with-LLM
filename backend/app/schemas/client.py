from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class ClientResponse(BaseModel):
    id: str
    name: str
    institution_type: str
    location: Optional[str] = None
    status: str
    created_at: datetime
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)

class ClientTaskDatasetMeta(BaseModel):
    dataset_name: str
    healthcare_task: str
    sample_count: int
    feature_count: int
    target_variable: str
    class_distribution: Dict[str, int]
    cohort_description: str

class ClientPrivateMetaResponse(BaseModel):
    client_id: str
    institution_name: str
    institution_type: str = "Hospital"
    privacy_status: str = "Strict Local Isolation (No raw records sent to server)"
    diabetes: ClientTaskDatasetMeta
    heart_disease: ClientTaskDatasetMeta

    model_config = ConfigDict(from_attributes=True)

class LocalTrainingRequest(BaseModel):
    local_epochs: Optional[int] = 3
    learning_rate: Optional[float] = 0.01
    batch_size: Optional[int] = 16
    dataset_scale: Optional[str] = "standard"

class LocalTrainingResponse(BaseModel):
    client_id: str
    healthcare_task: str
    dataset_scale: str = "standard"
    sample_count: int
    train_samples: int
    val_samples: int
    epochs_trained: int
    learning_rate: float
    batch_size: int
    gradient_steps: int = 0
    training_time_ms: int = 0
    initial_loss: float
    final_loss: float
    loss_history: list[float]
    val_loss_history: list[float] = []
    val_accuracy_history: list[float] = []
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    l2_norm: float
    update_size_kb: float
    delta_base64: str
    timestamp: str

class ClientUpdateSubmission(BaseModel):
    sample_count: int
    epochs_trained: int
    accuracy: float
    loss: Optional[float] = None
    l2_norm: float
    update_size_kb: float
    training_time_ms: Optional[int] = None
    delta_base64: Optional[str] = None
    loss_history: Optional[list[float]] = None
    val_loss_history: Optional[list[float]] = None
    val_accuracy_history: Optional[list[float]] = None
    gradient_steps: Optional[int] = None

