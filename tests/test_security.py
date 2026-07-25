from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.config import Settings
from app.models.auth import User
from app.models.enums import UserRole, UserStatus
from app.security import JWTService, PasswordService
from app.services.exceptions import InvalidAccessTokenError


def auth_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "jwt_secret_key": "a" * 48,
        "jwt_issuer": "test-waga",
        "jwt_audience": "test-api",
        "access_token_minutes": 15,
    }
    values.update(overrides)
    return Settings.model_validate(values)


def make_user() -> User:
    return User(
        id=uuid4(),
        email="person@example.com",
        password_hash="unused",
        role=UserRole.OPERATOR,
        status=UserStatus.ACTIVE,
        auth_version=3,
        failed_login_attempts=0,
    )


async def test_password_service_uses_argon2id() -> None:
    passwords = PasswordService()

    password_hash = await passwords.hash("correct horse battery staple")

    assert password_hash.startswith("$argon2id$")
    assert await passwords.verify("correct horse battery staple", password_hash)
    assert not await passwords.verify("wrong password", password_hash)
    assert not await passwords.verify("password", "not-a-supported-hash")


def test_jwt_round_trip_validates_identity_role_and_version() -> None:
    user = make_user()
    jwt_service = JWTService(auth_settings())

    token = jwt_service.create_access_token(user, datetime.now(UTC))
    claims = jwt_service.decode_access_token(token)

    assert claims.user_id == user.id
    assert claims.role == UserRole.OPERATOR
    assert claims.auth_version == 3
    assert jwt_service.expires_in_seconds == 900


def test_jwt_rejects_the_wrong_audience() -> None:
    user = make_user()
    token = JWTService(auth_settings()).create_access_token(user, datetime.now(UTC))
    other_audience = JWTService(auth_settings(jwt_audience="another-api"))

    with pytest.raises(InvalidAccessTokenError):
        other_audience.decode_access_token(token)
