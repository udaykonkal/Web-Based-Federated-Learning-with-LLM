from typing import Dict, Any, List
from pydantic import BaseModel

class AdminHealthResponse(BaseModel):
    status: str = "operational"
    role: str = "admin"
    coordinator: str = "Federated Learning Central Server"
    active_clients: int
    datasets_count: int
    models_count: int
    experiments_count: int

class AdminOverviewStats(BaseModel):
    total_clients: int
    active_experiments: int
    total_rounds_executed: int
    global_accuracy_average: float
    security_alerts_count: int
    communication_bytes_saved: int
