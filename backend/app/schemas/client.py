from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, model_validator

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
    dice_coefficient: Optional[float] = None
    l2_norm: float
    update_size_kb: float
    logs: list[str] = []
    delta_base64: str
    timestamp: str

class ClientUpdateSubmission(BaseModel):
    sample_count: int = 100
    epochs_trained: int = 3
    accuracy: float = 0.5
    loss: Optional[float] = None
    dice_coefficient: Optional[float] = None
    l2_norm: float = 1.0
    update_size_kb: float = 1.0
    training_time_ms: Optional[int] = None
    delta_base64: Optional[str] = None
    loss_history: Optional[list[float]] = None
    val_loss_history: Optional[list[float]] = None
    val_accuracy_history: Optional[list[float]] = None
    gradient_steps: Optional[int] = None

    @model_validator(mode='before')
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize sample_count aliases
            if data.get("sample_count") is None:
                data["sample_count"] = data.get("n_samples") or data.get("samples") or data.get("num_samples") or data.get("train_samples") or 100
            # Normalize epochs_trained aliases
            if data.get("epochs_trained") is None:
                data["epochs_trained"] = data.get("epochs") or data.get("epoch") or data.get("local_epochs") or data.get("round") or 3
            # Normalize accuracy aliases
            if data.get("accuracy") is None and data.get("acc") is not None:
                data["accuracy"] = data["acc"]
            # Normalize l2_norm aliases
            if data.get("l2_norm") is None and data.get("norm") is not None:
                data["l2_norm"] = data["norm"]
            # Normalize loss
            if data.get("loss") is None:
                data["loss"] = data.get("final_loss") or 0.4
            # Calculate update_size_kb if omitted
            if data.get("update_size_kb") is None:
                if data.get("delta_base64"):
                    data["update_size_kb"] = round(len(data["delta_base64"]) * 0.75 / 1024, 2)
                else:
                    data["update_size_kb"] = 1.0
        return data

class ModelDiscussionCreate(BaseModel):
    title: str
    content: str

class ModelDiscussionResponse(BaseModel):
    id: int
    model_id: int
    author_id: str
    author_name: str
    author_role: str
    title: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PipelineProposalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    architecture: Optional[str] = "MLP"
    code_snippet: str

class PipelineProposalResponse(BaseModel):
    id: int
    model_id: int
    author_id: str
    author_name: str
    title: str
    description: Optional[str] = None
    architecture: str
    code_snippet: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PipelineValidationRequest(BaseModel):
    code_snippet: str
    hyperparameters: Optional[Dict[str, Any]] = None


