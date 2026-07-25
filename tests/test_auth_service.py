from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.config import Settings
from app.models.auth import AuthSession, User
from app.models.contributors import Contributor
from app.models.enums import UserRole, UserStatus
from app.security import AccessTokenClaims
from app.services.auth import AuthService
from app.services.exceptions import (
    CurrentPasswordInvalidError,
    EmailAlreadyRegisteredError,
    InitialAdminAlreadyExistsError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    PasswordReuseError,
)


class FakeDatabaseSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    def add(self, user: User) -> None:
        self.users[user.id] = user

    async def get_by_email(
        self,
        email: str,
        *,
        for_update: bool = False,
    ) -> User | None:
        _ = for_update
        return next((user for user in self.users.values() if user.email == email), None)

    async def get_by_id(
        self,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> User | None:
        _ = for_update
        return self.users.get(user_id)

    async def has_admin(self) -> bool:
        return any(user.role == UserRole.ADMIN for user in self.users.values())


class FakeAuthSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[str, AuthSession] = {}

    def add(self, auth_session: AuthSession) -> None:
        self.sessions[auth_session.refresh_token_hash] = auth_session

    async def get_by_refresh_hash(
        self,
        refresh_token_hash: str,
        *,
        for_update: bool = False,
    ) -> AuthSession | None:
        _ = for_update
        return self.sessions.get(refresh_token_hash)

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        for auth_session in self.sessions.values():
            if auth_session.session_family_id == family_id and auth_session.revoked_at is None:
                auth_session.revoked_at = revoked_at

    async def revoke_all_for_user(self, user_id: UUID, revoked_at: datetime) -> None:
        for auth_session in self.sessions.values():
            if auth_session.user_id == user_id and auth_session.revoked_at is None:
                auth_session.revoked_at = revoked_at


class FakeContributorRepository:
    def __init__(self) -> None:
        self.contributors: list[Contributor] = []

    def add(self, contributor: Contributor) -> None:
        self.contributors.append(contributor)


class FakeInviteTokenRepository:
    def __init__(self) -> None:
        self.tokens: dict[str, object] = {}

    def add(self, invite_token: object) -> None:
        pass

    async def get_by_hash(
        self,
        token_hash: str,
        *,
        for_update: bool = False,
    ) -> None:
        _ = for_update
        return None


class FakePasswordService:
    def __init__(self) -> None:
        self.dummy_verifications = 0

    async def hash(self, password: str) -> str:
        return f"hashed:{password}"

    async def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"

    async def verify_dummy(self, password: str) -> None:
        _ = password
        self.dummy_verifications += 1


class FakeJWTService:
    expires_in_seconds = 900

    def __init__(self) -> None:
        self.claims: AccessTokenClaims | None = None

    def create_access_token(self, user: User, now: datetime) -> str:
        _ = now
        return f"access:{user.id}:{user.auth_version}"

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        _ = token
        if self.claims is None:
            raise InvalidAccessTokenError
        return self.claims


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def make_settings() -> Settings:
    return Settings.model_validate(
        {
            "jwt_secret_key": "a" * 48,
            "password_min_length": 8,
            "password_max_length": 128,
            "max_failed_login_attempts": 5,
            "login_lock_minutes": 15,
            "refresh_token_days": 30,
        }
    )


def make_service() -> SimpleNamespace:
    database = FakeDatabaseSession()
    users = FakeUserRepository()
    auth_sessions = FakeAuthSessionRepository()
    contributors = FakeContributorRepository()
    invite_tokens = FakeInviteTokenRepository()
    passwords = FakePasswordService()
    jwt_service = FakeJWTService()
    clock = MutableClock(datetime(2026, 7, 25, 12, 0, tzinfo=UTC))
    service = AuthService(
        database,  # type: ignore[arg-type]
        users,  # type: ignore[arg-type]
        auth_sessions,  # type: ignore[arg-type]
        contributors,  # type: ignore[arg-type]
        invite_tokens,  # type: ignore[arg-type]
        passwords,  # type: ignore[arg-type]
        jwt_service,  # type: ignore[arg-type]
        make_settings(),
        clock,
    )
    return SimpleNamespace(
        service=service,
        database=database,
        users=users,
        auth_sessions=auth_sessions,
        contributors=contributors,
        invite_tokens=invite_tokens,
        passwords=passwords,
        jwt_service=jwt_service,
        clock=clock,
    )


def add_user(
    context: SimpleNamespace,
    *,
    password: str = "valid-password",
    role: UserRole = UserRole.CONTRIBUTOR,
) -> User:
    user = User(
        id=uuid4(),
        email="person@example.com",
        password_hash=f"hashed:{password}",
        role=role,
        status=UserStatus.ACTIVE,
        auth_version=1,
        failed_login_attempts=0,
    )
    context.users.add(user)
    return user


async def test_ensure_admin_user_is_idempotent() -> None:
    context = make_service()

    user, created = await context.service.ensure_admin_user(
        "admin@waga.com",
        "valid-password",
        "Super Admin",
    )
    assert created is True
    assert user.role == UserRole.ADMIN

    again, created_again = await context.service.ensure_admin_user(
        "admin@waga.com",
        "valid-password",
        "Super Admin",
    )
    assert created_again is False
    assert again.id == user.id


async def test_login_locks_account_after_five_failures() -> None:
    context = make_service()
    user = add_user(context)

    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            await context.service.login(user.email, "wrong-password")

    assert user.failed_login_attempts == 5
    assert user.locked_until == context.clock.now + timedelta(minutes=15)
    with pytest.raises(InvalidCredentialsError):
        await context.service.login(user.email, "valid-password")


async def test_successful_login_resets_failures_and_creates_session() -> None:
    context = make_service()
    user = add_user(context)
    user.failed_login_attempts = 2
    user.locked_until = context.clock.now - timedelta(minutes=1)

    tokens = await context.service.login(user.email, "valid-password")

    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    assert user.last_login_at == context.clock.now
    assert context.service.hash_refresh_token(tokens.refresh_token) in (
        context.auth_sessions.sessions
    )


async def test_unknown_login_runs_dummy_password_verification() -> None:
    context = make_service()

    with pytest.raises(InvalidCredentialsError):
        await context.service.login("missing@example.com", "some-password")

    assert context.passwords.dummy_verifications == 1


async def test_refresh_rotation_and_reuse_revoke_the_family() -> None:
    context = make_service()
    user = add_user(context)
    initial = await context.service.login(user.email, "valid-password")

    rotated = await context.service.refresh(initial.refresh_token)
    old_session = context.auth_sessions.sessions[
        context.service.hash_refresh_token(initial.refresh_token)
    ]
    new_session = context.auth_sessions.sessions[
        context.service.hash_refresh_token(rotated.refresh_token)
    ]
    assert old_session.revoked_at == context.clock.now
    assert old_session.replaced_by_session_id == new_session.id
    assert new_session.revoked_at is None

    with pytest.raises(InvalidRefreshTokenError):
        await context.service.refresh(initial.refresh_token)

    assert new_session.revoked_at == context.clock.now


async def test_logout_all_invalidates_access_version_and_sessions() -> None:
    context = make_service()
    user = add_user(context)
    refresh_token, auth_session = context.service._new_auth_session(user.id)
    _ = refresh_token
    context.auth_sessions.add(auth_session)

    await context.service.logout_all(user.id)

    assert user.auth_version == 2
    assert auth_session.revoked_at == context.clock.now


async def test_change_password_revokes_old_sessions_and_issues_a_new_one() -> None:
    context = make_service()
    user = add_user(context)
    _, old_session = context.service._new_auth_session(user.id)
    context.auth_sessions.add(old_session)

    tokens = await context.service.change_password(
        user.id,
        "valid-password",
        "different-password",
    )

    new_session = context.auth_sessions.sessions[
        context.service.hash_refresh_token(tokens.refresh_token)
    ]
    assert user.password_hash == "hashed:different-password"
    assert user.auth_version == 2
    assert old_session.revoked_at == context.clock.now
    assert new_session.revoked_at is None


async def test_change_password_rejects_wrong_or_reused_password() -> None:
    context = make_service()
    user = add_user(context)

    with pytest.raises(CurrentPasswordInvalidError):
        await context.service.change_password(
            user.id,
            "wrong-password",
            "different-password",
        )
    with pytest.raises(PasswordReuseError):
        await context.service.change_password(
            user.id,
            "valid-password",
            "valid-password",
        )


async def test_access_authentication_rejects_auth_version_mismatch() -> None:
    context = make_service()
    user = add_user(context, role=UserRole.OPERATOR)
    context.jwt_service.claims = AccessTokenClaims(
        user_id=user.id,
        role=user.role,
        auth_version=0,
        token_id=uuid4(),
    )

    with pytest.raises(InvalidAccessTokenError):
        await context.service.authenticate_access_token("access-token")


async def test_access_authentication_rejects_disabled_user() -> None:
    context = make_service()
    user = add_user(context)
    user.status = UserStatus.DISABLED
    context.jwt_service.claims = AccessTokenClaims(
        user_id=user.id,
        role=user.role,
        auth_version=user.auth_version,
        token_id=uuid4(),
    )

    with pytest.raises(InvalidAccessTokenError):
        await context.service.authenticate_access_token("access-token")


async def test_initial_admin_can_only_be_created_once() -> None:
    context = make_service()

    admin = await context.service.create_initial_admin(
        "admin@example.com",
        "valid-password",
        "Administrator",
    )

    assert admin.role == UserRole.ADMIN
    with pytest.raises(InitialAdminAlreadyExistsError):
        await context.service.create_initial_admin(
            "other-admin@example.com",
            "valid-password",
            None,
        )
