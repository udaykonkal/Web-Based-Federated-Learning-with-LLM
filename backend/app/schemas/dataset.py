from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

class DatasetResponse(BaseModel):
    id: int
    name: str
    healthcare_task: str
    filename: str
    record_count: int
    feature_count: int
    target_variable: str
    class_distribution: Dict[str, int]
    feature_names: List[str]
    status: str
    is_admin_managed: bool
    is_distributed: bool = False
    distributed_at: Optional[datetime] = None
    created_at: datetime
    disclaimer: str = "Benchmark clinical dataset for federated learning experimentation."
    summary_stats: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class DatasetStatusUpdate(BaseModel):
    status: str  # "active" or "inactive"

class DatasetUploadResponse(BaseModel):
    message: str
    dataset: DatasetResponse
