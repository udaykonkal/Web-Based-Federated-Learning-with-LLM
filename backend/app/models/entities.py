from datetime import datetime, timezone
import enum
from typing import Optional, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CLIENT = "client"

class ModelStatus(str, enum.Enum):
    DRAFT = "draft"
    UPLOADED = "uploaded"
    PUBLISHED = "published"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class ExperimentStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class TrainingStatus(str, enum.Enum):
    READY = "ready"
    WAITING = "waiting"
    TRAINING = "training"
    TRAINING_COMPLETED = "training_completed"
    UPDATE_GENERATED = "update_generated"
    UPDATE_SUBMITTED = "update_submitted"
    VERIFICATION_PENDING = "verification_pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    AGGREGATED = "aggregated"

class ExperimentMode(str, enum.Enum):
    BASELINE = "baseline"
    PROPOSED = "proposed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default=UserRole.CLIENT.value)
    client_id = Column(String(50), ForeignKey("clients.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="users")

class Client(Base):
    __tablename__ = "clients"

    id = Column(String(50), primary_key=True, index=True)  # "client_1", "client_2", "client_3"
    name = Column(String(255), nullable=False)             # "Hospital/Clinic A"
    institution_type = Column(String(100), default="Hospital")
    location = Column(String(255), nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="client")
    participations = relationship("ClientParticipation", back_populates="client")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    healthcare_task = Column(String(100), nullable=False)  # "diabetes_prediction", "heart_disease_prediction"
    filename = Column(String(255), nullable=False)
    record_count = Column(Integer, default=0)
    feature_count = Column(Integer, default=0)
    target_variable = Column(String(100), nullable=False)
    class_distribution = Column(JSON, default=dict)
    feature_names = Column(JSON, default=list)
    status = Column(String(50), default="active")
    is_admin_managed = Column(Boolean, default=True)
    is_distributed = Column(Boolean, default=False)   # True = Admin published this dataset to all clients
    distributed_at = Column(DateTime, nullable=True)   # When admin distributed it
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    models = relationship("MLModel", back_populates="dataset")

class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # "Diabetes Prediction", "Heart Disease Prediction"
    healthcare_task = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    architecture = Column(String(100), default="MLP")
    version = Column(String(50), default="v1.0")
    status = Column(String(50), default=ModelStatus.DRAFT.value)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    target_variable = Column(String(100), nullable=False)
    input_features = Column(JSON, default=list)
    hyperparameters = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="models")
    experiments = relationship("Experiment", back_populates="model")

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    mode = Column(String(50), default=ExperimentMode.PROPOSED.value)  # baseline vs proposed
    total_rounds = Column(Integer, default=5)
    current_round = Column(Integer, default=0)
    status = Column(String(50), default=ExperimentStatus.CREATED.value)
    
    # Configuration flags
    client_selection_mode = Column(String(50), default="adaptive")  # "random" vs "adaptive"
    security_enabled = Column(Boolean, default=True)
    communication_optimization_enabled = Column(Boolean, default=True)
    llm_enabled = Column(Boolean, default=True)
    
    # Hyperparameters
    local_epochs = Column(Integer, default=3)
    learning_rate = Column(Float, default=0.01)
    batch_size = Column(Integer, default=16)

    final_accuracy = Column(Float, nullable=True)
    final_loss = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    model = relationship("MLModel", back_populates="experiments")
    rounds = relationship("FLRound", back_populates="experiment")
    security_events = relationship("SecurityEvent", back_populates="experiment")
    llm_recommendations = relationship("LLMRecommendation", back_populates="experiment")

class FLRound(Base):
    __tablename__ = "fl_rounds"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    global_accuracy = Column(Float, nullable=True)
    global_loss = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    aggregation_metrics = Column(JSON, default=dict)
    global_model_path = Column(String(255), nullable=True)
    
    selected_clients = Column(JSON, default=list)
    accepted_updates_count = Column(Integer, default=0)
    rejected_updates_count = Column(Integer, default=0)
    total_communication_bytes = Column(Integer, default=0)
    communication_savings_bytes = Column(Integer, default=0)

    experiment = relationship("Experiment", back_populates="rounds")
    participations = relationship("ClientParticipation", back_populates="round")
    updates = relationship("ModelUpdate", back_populates="round")

class ClientParticipation(Base):
    __tablename__ = "client_participations"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("fl_rounds.id"), nullable=False)
    client_id = Column(String(50), ForeignKey("clients.id"), nullable=False)
    
    is_selected = Column(Boolean, default=False)
    selection_score = Column(Float, default=0.0)
    score_breakdown = Column(JSON, default=dict)
    training_status = Column(String(50), default=TrainingStatus.WAITING.value)
    
    local_sample_count = Column(Integer, default=0)
    local_epochs = Column(Integer, default=3)
    local_accuracy = Column(Float, nullable=True)
    local_loss = Column(Float, nullable=True)
    training_time_ms = Column(Integer, nullable=True)
    update_size_bytes = Column(Integer, default=0)
    
    update_verified = Column(Boolean, default=False)
    is_accepted = Column(Boolean, default=False)
    rejection_reason = Column(String(255), nullable=True)
    aggregation_weight = Column(Float, default=0.0)

    round = relationship("FLRound", back_populates="participations")
    client = relationship("Client", back_populates="participations")

class ModelUpdate(Base):
    __tablename__ = "model_updates"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("fl_rounds.id"), nullable=False)
    client_id = Column(String(50), nullable=False)
    
    update_norm = Column(Float, nullable=True)
    cosine_similarity = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    is_malicious_simulated = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)
    
    original_size_bytes = Column(Integer, default=0)
    compressed_size_bytes = Column(Integer, default=0)
    compression_ratio = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    round = relationship("FLRound", back_populates="updates")

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    client_id = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)  # "anomaly_detected", "sign_flipping", "extreme_magnitude"
    severity = Column(String(50), default="warning")  # "info", "warning", "critical"
    anomaly_score = Column(Float, default=0.0)
    details = Column(JSON, default=dict)
    recommended_action = Column(String(255), nullable=True)
    action_taken = Column(String(100), default="rejected")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    experiment = relationship("Experiment", back_populates="security_events")

class LLMRecommendation(Base):
    __tablename__ = "llm_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    recommendation_type = Column(String(100), nullable=False)  # "client_selection", "security_analysis", "training_analysis", "communication_analysis"
    source = Column(String(50), default="llm")                # "llm" or "deterministic_fallback"
    payload = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    experiment = relationship("Experiment", back_populates="llm_recommendations")
