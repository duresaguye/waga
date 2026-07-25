from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from anyio import to_thread
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import Settings
from app.models.auth import User
from app.models.enums import UserRole
from app.services.exceptions import InvalidAccessTokenError


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: UUID
    role: UserRole
    auth_version: int
    token_id: UUID


class PasswordService:
    def __init__(self) -> None:
        self._password_hash = PasswordHash((Argon2Hasher(),))
        self._dummy_hash = self._password_hash.hash("not-a-real-user-password")

    async def hash(self, password: str) -> str:
        return await to_thread.run_sync(self._password_hash.hash, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        try:
            return await to_thread.run_sync(
                self._password_hash.verify,
                password,
                password_hash,
            )
        except (TypeError, UnknownHashError, ValueError):
            return False

    async def verify_dummy(self, password: str) -> None:
        await self.verify(password, self._dummy_hash)


class JWTService:
    algorithm = "HS256"

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key.get_secret_value()
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._access_token_minutes = settings.access_token_minutes

    @property
    def expires_in_seconds(self) -> int:
        return self._access_token_minutes * 60

    def create_access_token(self, user: User, now: datetime | None = None) -> str:
        issued_at = now or datetime.now(UTC)
        expires_at = issued_at + timedelta(minutes=self._access_token_minutes)
        payload = {
            "sub": str(user.id),
            "role": user.role.value,
            "ver": user.auth_version,
            "jti": str(uuid4()),
            "iat": issued_at,
            "exp": expires_at,
            "iss": self._issuer,
            "aud": self._audience,
            "typ": "access",
        }
        return jwt.encode(payload, self._secret, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self.algorithm],
                audience=self._audience,
                issuer=self._issuer,
                options={
                    "require": [
                        "sub",
                        "role",
                        "ver",
                        "jti",
                        "iat",
                        "exp",
                        "iss",
                        "aud",
                        "typ",
                    ]
                },
            )
            if payload["typ"] != "access":
                raise InvalidAccessTokenError
            auth_version = payload["ver"]
            if isinstance(auth_version, bool) or not isinstance(auth_version, int):
                raise InvalidAccessTokenError
            return AccessTokenClaims(
                user_id=UUID(payload["sub"]),
                role=UserRole(payload["role"]),
                auth_version=auth_version,
                token_id=UUID(payload["jti"]),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            jwt.PyJWTError,
        ) as error:
            raise InvalidAccessTokenError from error
