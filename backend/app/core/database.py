from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

from sqlalchemy import text

async def init_db() -> None:
    """Initialize database tables and run lightweight column upgrades for SQLite."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Ensure new columns exist on SQLite tables
        for table, col, col_type in [
            ("experiments", "final_accuracy", "FLOAT"),
            ("experiments", "final_loss", "FLOAT"),
            ("fl_rounds", "precision", "FLOAT"),
            ("fl_rounds", "recall", "FLOAT"),
            ("fl_rounds", "f1_score", "FLOAT"),
            ("fl_rounds", "aggregation_metrics", "JSON"),
            ("client_participations", "training_status", "VARCHAR(50)"),
            ("client_participations", "update_size_bytes", "INTEGER"),
        ]:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
            except Exception:
                pass  # Column already exists
