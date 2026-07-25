import pytest
from pydantic import ValidationError

from app.config import Settings


def test_standard_postgresql_url_uses_asyncpg_driver() -> None:
    settings = Settings.model_validate(
        {"database_url": "postgresql://postgres:password@db.example.com:5432/postgres"}
    )

    assert settings.database_url == (
        "postgresql+asyncpg://postgres:password@db.example.com:5432/postgres"
    )


def test_production_requires_a_strong_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="WAGA_JWT_SECRET_KEY"):
        Settings.model_validate(
            {
                "environment": "production",
                "jwt_secret_key": "too-short",
            }
        )


def test_auth_duration_configuration_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="WAGA_ACCESS_TOKEN_MINUTES"):
        Settings.model_validate({"access_token_minutes": 0})
