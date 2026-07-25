from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_auth_service, get_current_user, require_roles
from app.main import app
from app.models.auth import User
from app.models.enums import UserRole, UserStatus
from app.services.auth import IssuedTokens
from app.services.exceptions import InvalidCredentialsError


class FakeAuthService:
    async def register(
        self,
        email: str,
        password: str,
        display_name: str | None,
    ) -> IssuedTokens:
        _ = (email, password, display_name)
        return IssuedTokens("access-token", "refresh-token", 900)

    async def login(self, email: str, password: str) -> IssuedTokens:
        _ = (email, password)
        raise InvalidCredentialsError


async def test_register_returns_json_token_pair() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "person@example.com",
                    "password": "valid-password",
                    "display_name": "Person",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
        "expires_in": 900,
    }


async def test_login_uses_generic_invalid_credentials_response() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "person@example.com", "password": "wrong-password"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


async def test_me_requires_and_returns_the_current_user() -> None:
    current_user = User(
        id=uuid4(),
        email="operator@example.com",
        password_hash="unused",
        display_name="Operator",
        role=UserRole.OPERATOR,
        status=UserStatus.ACTIVE,
        auth_version=1,
        failed_login_attempts=0,
        created_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_current_user] = lambda: current_user
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["email"] == "operator@example.com"
    assert response.json()["role"] == "operator"


async def test_role_dependency_rejects_an_unapproved_role() -> None:
    contributor = User(
        id=uuid4(),
        email="contributor@example.com",
        password_hash="unused",
        role=UserRole.CONTRIBUTOR,
        status=UserStatus.ACTIVE,
        auth_version=1,
        failed_login_attempts=0,
    )
    dependency = require_roles(UserRole.ADMIN, UserRole.OPERATOR)

    with pytest.raises(HTTPException) as error:
        await dependency(contributor)

    assert error.value.status_code == 403
