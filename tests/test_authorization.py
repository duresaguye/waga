from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.dependencies import (
    admin_role_dependency,
    get_admin_dashboard_service,
    get_current_subscriber,
    get_current_user,
)
from app.main import app
from app.models.auth import User
from app.models.enums import UserRole, UserStatus


def _user(role: UserRole, *, email: str | None = None) -> User:
    return User(
        id=uuid4(),
        email=email or f"{role.value}@example.com",
        password_hash="unused",
        display_name=role.value.title(),
        role=role,
        status=UserStatus.ACTIVE,
        auth_version=1,
        failed_login_attempts=0,
        created_at=datetime(2026, 7, 25, tzinfo=UTC),
    )


class FakeAdminDashboardService:
    async def get_dashboard(self) -> dict:
        return {"stats": {"pending_agents": 0}}


class FakeSubscriptionService:
    async def ensure_subscription(self, user: User) -> None:
        _ = user


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_access_admin_routes() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "role",
    [
        UserRole.SUBSCRIBER,
        UserRole.CONTRIBUTOR,
        UserRole.VIEWER,
    ],
)
@pytest.mark.asyncio
async def test_non_admin_roles_cannot_access_admin_dashboard(role: UserRole) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(role)
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/admin/dashboard")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.OPERATOR])
@pytest.mark.asyncio
async def test_admin_roles_can_access_admin_dashboard(role: UserRole) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(role)
    app.dependency_overrides[get_admin_dashboard_service] = (
        lambda: FakeAdminDashboardService()
    )
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/admin/dashboard")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200


async def test_admin_role_dependency_rejects_subscriber() -> None:
    with pytest.raises(HTTPException) as error:
        await admin_role_dependency(_user(UserRole.SUBSCRIBER))
    assert error.value.status_code == 403


async def test_get_current_subscriber_rejects_non_subscriber_roles() -> None:
    fake = FakeSubscriptionService()
    for role in (
        UserRole.ADMIN,
        UserRole.OPERATOR,
        UserRole.CONTRIBUTOR,
        UserRole.VIEWER,
    ):
        with pytest.raises(HTTPException) as error:
            await get_current_subscriber(_user(role), fake)  # type: ignore[arg-type]
        assert error.value.status_code == 403
        assert error.value.detail == "Subscriber account required"


async def test_get_current_subscriber_allows_subscriber() -> None:
    fake = FakeSubscriptionService()
    subscriber = _user(UserRole.SUBSCRIBER)
    result = await get_current_subscriber(subscriber, fake)  # type: ignore[arg-type]
    assert result is subscriber


@pytest.mark.asyncio
async def test_public_agent_review_hooks_removed() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        accept = await client.post("/api/v1/agents/12345/review/accept")
        flag = await client.post("/api/v1/agents/12345/review/flag")
    assert accept.status_code == 404
    assert flag.status_code == 404
