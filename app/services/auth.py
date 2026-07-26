from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.admin import InviteToken
from app.models.auth import AuthSession, User
from app.models.enums import UserRole, UserStatus
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.contributors import ContributorRepository
from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.users import UserRepository
from app.security import JWTService, PasswordService
from app.services.exceptions import (
    CurrentPasswordInvalidError,
    EmailAlreadyRegisteredError,
    InitialAdminAlreadyExistsError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InviteTokenAlreadyUsedError,
    InviteTokenExpiredError,
    InviteTokenNotFoundError,
    PasswordPolicyError,
    PasswordReuseError,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def _is_unique_violation(error: IntegrityError) -> bool:
    return getattr(error.orig, "pgcode", None) == "23505"


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        auth_sessions: AuthSessionRepository,
        contributors: ContributorRepository,
        invite_tokens: InviteTokenRepository,
        passwords: PasswordService,
        jwt_service: JWTService,
        settings: Settings,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._session = session
        self._users = users
        self._auth_sessions = auth_sessions
        self._contributors = contributors
        self._invite_tokens = invite_tokens
        self._passwords = passwords
        self._jwt = jwt_service
        self._settings = settings
        self._clock = clock

    async def login(self, email: str, password: str) -> IssuedTokens:
        normalized_email = self._normalize_email(email)
        user = await self._users.get_by_email(normalized_email, for_update=True)
        if user is None:
            await self._passwords.verify_dummy(password)
            await self._session.rollback()
            raise InvalidCredentialsError

        password_valid = await self._passwords.verify(password, user.password_hash)
        now = self._clock()
        is_locked = user.locked_until is not None and user.locked_until > now
        if user.status != UserStatus.ACTIVE or is_locked:
            await self._session.rollback()
            raise InvalidCredentialsError

        if not password_valid:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self._settings.max_failed_login_attempts:
                user.locked_until = now + timedelta(minutes=self._settings.login_lock_minutes)
            await self._session.commit()
            raise InvalidCredentialsError

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        refresh_token, auth_session = self._new_auth_session(user.id)
        self._auth_sessions.add(auth_session)
        await self._session.commit()
        return self._issued_tokens(user, refresh_token)

    async def refresh(self, refresh_token: str) -> IssuedTokens:
        token_hash = self.hash_refresh_token(refresh_token)
        current_session = await self._auth_sessions.get_by_refresh_hash(
            token_hash,
            for_update=True,
        )
        if current_session is None:
            await self._session.rollback()
            raise InvalidRefreshTokenError

        now = self._clock()
        if current_session.revoked_at is not None:
            if current_session.replaced_by_session_id is not None:
                await self._auth_sessions.revoke_family(
                    current_session.session_family_id,
                    now,
                )
                await self._session.commit()
            else:
                await self._session.rollback()
            raise InvalidRefreshTokenError

        if current_session.expires_at <= now:
            current_session.revoked_at = now
            await self._session.commit()
            raise InvalidRefreshTokenError

        user = await self._users.get_by_id(current_session.user_id, for_update=True)
        if user is None or user.status != UserStatus.ACTIVE:
            await self._auth_sessions.revoke_family(
                current_session.session_family_id,
                now,
            )
            await self._session.commit()
            raise InvalidRefreshTokenError

        new_refresh_token, replacement = self._new_auth_session(
            user.id,
            family_id=current_session.session_family_id,
        )
        # replaced_by_session_id is a self-referencing FK, so the replacement row must exist
        # before the old session can point at it.
        self._auth_sessions.add(replacement)
        await self._session.flush()
        current_session.last_used_at = now
        current_session.revoked_at = now
        current_session.replaced_by_session_id = replacement.id
        await self._session.commit()
        return self._issued_tokens(user, new_refresh_token)

    async def logout(self, refresh_token: str) -> None:
        current_session = await self._auth_sessions.get_by_refresh_hash(
            self.hash_refresh_token(refresh_token),
            for_update=True,
        )
        if current_session is None or current_session.revoked_at is not None:
            await self._session.rollback()
            return
        current_session.revoked_at = self._clock()
        await self._session.commit()

    async def logout_all(self, user_id: UUID) -> None:
        user = await self._users.get_by_id(user_id, for_update=True)
        if user is None or user.status != UserStatus.ACTIVE:
            await self._session.rollback()
            raise InvalidAccessTokenError
        now = self._clock()
        user.auth_version += 1
        await self._auth_sessions.revoke_all_for_user(user.id, now)
        await self._session.commit()

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> IssuedTokens:
        self._validate_password(new_password)
        user = await self._users.get_by_id(user_id, for_update=True)
        if user is None or user.status != UserStatus.ACTIVE:
            await self._session.rollback()
            raise InvalidAccessTokenError
        if not await self._passwords.verify(current_password, user.password_hash):
            await self._session.rollback()
            raise CurrentPasswordInvalidError
        if await self._passwords.verify(new_password, user.password_hash):
            await self._session.rollback()
            raise PasswordReuseError

        now = self._clock()
        user.password_hash = await self._passwords.hash(new_password)
        user.password_changed_at = now
        user.auth_version += 1
        await self._auth_sessions.revoke_all_for_user(user.id, now)
        refresh_token, auth_session = self._new_auth_session(user.id)
        self._auth_sessions.add(auth_session)
        await self._session.commit()
        return self._issued_tokens(user, refresh_token)

    async def authenticate_access_token(self, token: str) -> User:
        claims = self._jwt.decode_access_token(token)
        user = await self._users.get_by_id(claims.user_id)
        if (
            user is None
            or user.status != UserStatus.ACTIVE
            or user.auth_version != claims.auth_version
            or user.role != claims.role
        ):
            await self._session.rollback()
            raise InvalidAccessTokenError
        return user

    async def create_initial_admin(
        self,
        email: str,
        password: str,
        display_name: str | None,
    ) -> User:
        normalized_email = self._normalize_email(email)
        self._validate_password(password)
        if await self._users.has_admin():
            await self._session.rollback()
            raise InitialAdminAlreadyExistsError
        if await self._users.get_by_email(normalized_email) is not None:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError

        user = await self._new_admin_user(normalized_email, password, display_name)
        self._users.add(user)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if _is_unique_violation(error):
                raise EmailAlreadyRegisteredError from error
            raise
        return user

    async def ensure_admin_user(
        self,
        email: str,
        password: str,
        display_name: str | None,
    ) -> tuple[User, bool]:
        """Idempotent admin seed — creates the user only when the email is unused."""
        normalized_email = self._normalize_email(email)
        self._validate_password(password)
        existing = await self._users.get_by_email(normalized_email)
        if existing is not None:
            return existing, False

        user = await self._new_admin_user(normalized_email, password, display_name)
        self._users.add(user)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if _is_unique_violation(error):
                existing = await self._users.get_by_email(normalized_email)
                if existing is not None:
                    return existing, False
                raise EmailAlreadyRegisteredError from error
            raise
        return user, True

    async def _new_admin_user(
        self,
        normalized_email: str,
        password: str,
        display_name: str | None,
    ) -> User:
        return User(
            id=uuid4(),
            email=normalized_email,
            password_hash=await self._passwords.hash(password),
            display_name=display_name,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            auth_version=1,
            failed_login_attempts=0,
        )

    async def invite_user(
        self,
        email: str,
        role: UserRole,
        display_name: str | None,
    ) -> str:
        """Create a disabled user and return a raw invite token (64-char hex)."""
        normalized_email = self._normalize_email(email)
        if await self._users.get_by_email(normalized_email) is not None:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError

        now = self._clock()
        user = User(
            id=uuid4(),
            email=normalized_email,
            password_hash=await self._passwords.hash("pending-invite"),
            display_name=display_name,
            role=role,
            status=UserStatus.DISABLED,
            auth_version=1,
            failed_login_attempts=0,
        )
        raw_token = token_urlsafe(32)
        invite = InviteToken(
            id=uuid4(),
            user_id=user.id,
            token_hash=sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=now + timedelta(hours=24),
        )

        self._users.add(user)
        self._invite_tokens.add(invite)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if _is_unique_violation(error):
                raise EmailAlreadyRegisteredError from error
            raise
        return raw_token

    async def accept_invite(
        self,
        raw_token: str,
        password: str,
    ) -> IssuedTokens:
        """Validate invite token, activate user, set password, return tokens."""
        self._validate_password(password)
        token_hash = sha256(raw_token.encode("utf-8")).hexdigest()
        invite = await self._invite_tokens.get_by_hash(token_hash, for_update=True)
        if invite is None:
            await self._session.rollback()
            raise InviteTokenNotFoundError

        now = self._clock()
        if invite.accepted_at is not None:
            await self._session.rollback()
            raise InviteTokenAlreadyUsedError
        if invite.expires_at <= now:
            await self._session.rollback()
            raise InviteTokenExpiredError

        user = await self._users.get_by_id(invite.user_id, for_update=True)
        if user is None or user.status != UserStatus.DISABLED:
            await self._session.rollback()
            raise InviteTokenNotFoundError

        user.password_hash = await self._passwords.hash(password)
        user.password_changed_at = now
        user.status = UserStatus.ACTIVE
        invite.accepted_at = now

        refresh_token, auth_session = self._new_auth_session(user.id)
        self._auth_sessions.add(auth_session)
        await self._session.commit()
        return self._issued_tokens(user, refresh_token)

    @staticmethod
    def hash_refresh_token(refresh_token: str) -> str:
        return sha256(refresh_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def _validate_password(self, password: str) -> None:
        password_length = len(password)
        if not (
            self._settings.password_min_length
            <= password_length
            <= self._settings.password_max_length
        ):
            raise PasswordPolicyError(
                f"Password must be between {self._settings.password_min_length} "
                f"and {self._settings.password_max_length} characters"
            )

    def _new_auth_session(
        self,
        user_id: UUID,
        *,
        family_id: UUID | None = None,
    ) -> tuple[str, AuthSession]:
        now = self._clock()
        refresh_token = token_urlsafe(48)
        auth_session = AuthSession(
            id=uuid4(),
            user_id=user_id,
            refresh_token_hash=self.hash_refresh_token(refresh_token),
            session_family_id=family_id or uuid4(),
            expires_at=now + timedelta(days=self._settings.refresh_token_days),
        )
        return refresh_token, auth_session

    def _issued_tokens(self, user: User, refresh_token: str) -> IssuedTokens:
        return IssuedTokens(
            access_token=self._jwt.create_access_token(user, self._clock()),
            refresh_token=refresh_token,
            expires_in=self._jwt.expires_in_seconds,
        )
