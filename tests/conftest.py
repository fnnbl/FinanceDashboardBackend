from contextlib import asynccontextmanager

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.crud.category import seed_default_categories

TEST_DATABASE_URL = "sqlite+aiosqlite://"


# Replace production lifespan with no-op so tests don't touch Supabase
@asynccontextmanager
async def _test_lifespan(app):
    yield


app.router.lifespan_context = _test_lifespan


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        await seed_default_categories(session)
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# --- Helper functions (reusable across test modules) ---

async def register(client: AsyncClient, email="user@example.com", password="password123", name="Test User"):
    return await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
    })


async def get_token(client: AsyncClient, email="user@example.com", password="password123") -> str:
    r = await client.post("/api/v1/auth/token", data={"username": email, "password": password})
    return r.json()["access_token"]


async def auth(client: AsyncClient, email="user@example.com", password="password123") -> dict:
    token = await get_token(client, email, password)
    return {"Authorization": f"Bearer {token}"}


async def get_expense_category_id(client: AsyncClient, headers: dict) -> int:
    r = await client.get("/api/v1/categories/?type=expense", headers=headers)
    return r.json()[0]["id"]


async def get_income_category_id(client: AsyncClient, headers: dict) -> int:
    r = await client.get("/api/v1/categories/?type=income", headers=headers)
    return r.json()[0]["id"]


async def create_plan(client: AsyncClient, headers: dict, name="Testplan", description="") -> dict:
    r = await client.post("/api/v1/plans/", json={"name": name, "description": description}, headers=headers)
    return r.json()


async def create_budget_item(client: AsyncClient, headers: dict, plan_id: int, **overrides) -> dict:
    cat_id = await get_expense_category_id(client, headers)
    payload = {
        "description": "Testposten",
        "amount": 100.0,
        "type": "expense",
        "category_id": cat_id,
        "payment_rhythm": "monthly",
        "note": "",
        **overrides,
    }
    r = await client.post(f"/api/v1/plans/{plan_id}/items/", json=payload, headers=headers)
    return r


# --- Fixtures for common setups ---

@pytest_asyncio.fixture
async def auth_headers(client):
    await register(client)
    return await auth(client)


@pytest_asyncio.fixture
async def second_user_headers(client):
    await register(client, email="other@example.com", name="Other User")
    return await auth(client, email="other@example.com")
