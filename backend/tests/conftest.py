import pytest
import pytest_asyncio
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.database import init_db
from app.seed import seed_database

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Ensure database and seed data are initialized for test session."""
    await init_db()
    await seed_database()

@pytest_asyncio.fixture
async def async_client():
    """Asynchronous test client fixture using httpx ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
