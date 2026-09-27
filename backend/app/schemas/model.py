from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.entities import ModelStatus

class MLModelBase(BaseModel):
    name: str
    healthcare_task: str
    description: Optional[str] = None
    architecture: str = "MLP"
    version: str = "v1.0"
    target_variable: str
    input_features: List[str] = []
    hyperparameters: Dict[str, Any] = {}

class MLModelCreate(MLModelBase):
    dataset_id: Optional[int] = None
    status: str = ModelStatus.DRAFT.value

class MLModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None

class MLModelStatusUpdate(BaseModel):
    status: str  # draft, uploaded, published, active, inactive, archived

class MLModelResponse(MLModelBase):
    id: int
    status: str
    dataset_id: Optional[int] = None
    dataset_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    fl_enabled: bool = True

    model_config = ConfigDict(from_attributes=True)
