import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
# Allow DATA_DIR to be overridden by environment variable (used on Render)
_DATA_DIR_ENV = os.environ.get("DATA_DIR", "")
DATA_DIR = Path(_DATA_DIR_ENV) if _DATA_DIR_ENV else BASE_DIR / "data"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Web-Based Federated Learning Platform with LLM-Based Automation for Healthcare"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "fl-healthcare-production-secret-key-2026-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///./fl_healthcare.db"
    SYNC_DATABASE_URL: str = f"sqlite:///./fl_healthcare.db"

    # CORS — includes Vercel frontend + local dev
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://web-based-federated-learning-with-llm.vercel.app",
        "https://*.vercel.app",
        "*"
    ]

    # Data paths
    BASE_DIR: Path = BASE_DIR
    DATA_PATH: Path = DATA_DIR
    ADMIN_DATA_PATH: Path = DATA_DIR / "admin"
    CLIENTS_DATA_PATH: Path = DATA_DIR / "clients"
    EXPERIMENTS_DATA_PATH: Path = DATA_DIR / "experiments"

    # LLM Settings
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )

settings = Settings()

# Ensure directories exist
settings.DATA_PATH.mkdir(parents=True, exist_ok=True)
settings.ADMIN_DATA_PATH.mkdir(parents=True, exist_ok=True)
settings.CLIENTS_DATA_PATH.mkdir(parents=True, exist_ok=True)
for c in ["client_1", "client_2", "client_3"]:
    (settings.CLIENTS_DATA_PATH / c).mkdir(parents=True, exist_ok=True)
