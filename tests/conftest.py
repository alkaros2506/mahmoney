import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mahmoney.api.app import create_app
from mahmoney.api.deps import get_db
from mahmoney.auth import create_session
from mahmoney.models.enums import Category, ExpenseStatus, PaymentMethod, Source
from mahmoney.models.expense import Base, Expense


@pytest.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def app(engine) -> FastAPI:
    application = create_app()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    application.dependency_overrides[get_db] = override_get_db
    return application


def _get_auth_cookie() -> dict[str, str]:
    """Create a valid session and return the cookie header."""
    from starlette.responses import Response

    resp = Response()
    create_session(resp)
    # Extract the set-cookie header value
    for header_name, header_value in resp.raw_headers:
        if header_name == b"set-cookie":
            cookie_str = header_value.decode()
            # Parse "mahmoney_session=value; ..."
            cookie_pair = cookie_str.split(";")[0]
            return {"Cookie": cookie_pair}
    return {}


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    cookies = _get_auth_cookie()
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=cookies
    ) as c:
        yield c


@pytest.fixture
async def sample_expense(db_session: AsyncSession) -> Expense:
    expense = Expense(
        id=uuid.uuid4(),
        supplier_name="Test Supplier",
        supplier_country="GR",
        date=datetime(2026, 1, 15, tzinfo=UTC),
        total_amount=Decimal("100.00"),
        currency="EUR",
        payment_method=PaymentMethod.CARD,
        category=Category.OTHER,
        source=Source.MANUAL,
        status=ExpenseStatus.PENDING_REVIEW,
    )
    db_session.add(expense)
    await db_session.commit()
    await db_session.refresh(expense)
    return expense
