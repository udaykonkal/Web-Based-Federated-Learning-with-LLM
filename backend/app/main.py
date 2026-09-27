from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.api import api_v1_router
from app.seed import seed_database
from app.services.dataset_service import initialize_admin_healthcare_datasets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await seed_database()
    async with AsyncSessionLocal() as session:
        await initialize_admin_healthcare_datasets(session)
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-grade Web-Based Federated Learning Platform with LLM-Based Automation for Healthcare. "
        "Strictly enforces Admin coordinator vs isolated local training clients with zero raw patient data leakage."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "platform": settings.PROJECT_NAME,
        "status": "online",
        "side_a": "Central Server / Admin Coordinator (No local training)",
        "side_b": "3 Isolated Healthcare Clients (Local training only, zero raw data transmission)",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "fl-healthcare-backend"}
