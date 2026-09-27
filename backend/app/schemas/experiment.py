from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, model_validator

class ExperimentCreate(BaseModel):
    name: str
    healthcare_task: str
    model_id: int
    total_rounds: int = 3
    strategy: str = "FedAvg"  # "FedAvg" or "Adaptive_FedAvg"
    client_selection_mode: str = "adaptive"  # "adaptive" or "random"
    local_epochs: int = 3
    learning_rate: float = 0.01
    batch_size: int = 16

class FLRoundResponse(BaseModel):
    id: int
    experiment_id: int
    round_number: int
    status: str
    global_loss: Optional[float] = None
    global_accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    participating_clients: List[str] = []
    aggregation_metrics: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_from_orm(cls, data: Any) -> Any:
        if hasattr(data, "selected_clients"):
            return {
                "id": data.id,
                "experiment_id": data.experiment_id,
                "round_number": data.round_number,
                "status": data.status,
                "global_loss": data.global_loss,
                "global_accuracy": data.global_accuracy,
                "precision": data.precision,
                "recall": data.recall,
                "f1_score": data.f1_score,
                "participating_clients": data.selected_clients or [],
                "aggregation_metrics": data.aggregation_metrics or {},
                "started_at": data.started_at,
                "completed_at": data.completed_at
            }
        return data

class ExperimentResponse(BaseModel):
    id: int
    name: str
    healthcare_task: str
    model_id: int
    model_name: Optional[str] = None
    status: str
    current_round: int
    total_rounds: int
    strategy: str
    client_selection_mode: str = "adaptive"
    local_epochs: int = 3
    learning_rate: float = 0.01
    batch_size: int = 16
    final_accuracy: Optional[float] = None
    final_loss: Optional[float] = None
    created_at: datetime
    rounds: List[FLRoundResponse] = []

    model_config = ConfigDict(from_attributes=True)
