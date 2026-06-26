"""测试夹具：用内存 SQLite 跑 API，无需 Postgres/Redis/Celery。

被测端点（auth / banks / questions / quiz）只依赖数据库，因此可在 SQLite 上完整运行。
"""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 - 注册所有表
from app.database import Base, get_db
from app.main import app


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.state.test_sessionmaker = Session

    async def _get_db():
        async with Session() as s:
            yield s

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def auth_headers(client, role_sql=None):
    """注册并登录一个用户，返回 (headers, user_dict)。"""
    import uuid

    sfx = uuid.uuid4().hex[:8]
    email = f"t_{sfx}@e.com"
    reg = await client.post(
        "/auth/register", json={"email": email, "username": f"t_{sfx}", "password": "secret123"}
    )
    user = reg.json()
    login = await client.post(
        "/auth/login", data={"username": email, "password": "secret123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user


async def make_admin(user_id: str):
    """直接改库把用户提为 admin（测试里没有现成管理员可用）。"""
    import uuid

    from sqlalchemy import update

    from app.models.user import User, UserRole

    Session = app.state.test_sessionmaker
    async with Session() as s:
        await s.execute(
            update(User).where(User.id == uuid.UUID(user_id)).values(role=UserRole.admin)
        )
        await s.commit()
