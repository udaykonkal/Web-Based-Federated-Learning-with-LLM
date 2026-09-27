from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.client import router as client_router
from app.api.v1.telemetry import router as telemetry_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(client_router)
api_v1_router.include_router(telemetry_router)
