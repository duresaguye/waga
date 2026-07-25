from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db_session
from app.models.auth import User
from app.models.enums import UserRole
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.agent_applications import AgentApplicationRepository
from app.repositories.contributors import ContributorRepository
from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.repositories.reward_settings import RewardSettingsRepository
from app.repositories.submissions import SubmissionRepository
from app.repositories.users import UserRepository
from app.security import JWTService, PasswordService
from app.services.agent_applications import AgentApplicationService
from app.services.agent_score import AgentScoreService
from app.services.auth import AuthService
from app.services.exceptions import InvalidAccessTokenError
from app.services.reference_data import ReferenceDataService
from app.services.submissions import SubmissionService

bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    return UserRepository(session)


def get_auth_session_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthSessionRepository:
    return AuthSessionRepository(session)


def get_contributor_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ContributorRepository:
    return ContributorRepository(session)


def get_invite_token_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InviteTokenRepository:
    return InviteTokenRepository(session)


def get_reference_data_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReferenceDataRepository:
    return ReferenceDataRepository(session)


def get_reference_data_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
) -> ReferenceDataService:
    return ReferenceDataService(session, reference_data)


def get_reward_settings_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RewardSettingsRepository:
    return RewardSettingsRepository(session)


def get_agent_application_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentApplicationRepository:
    return AgentApplicationRepository(session)


def get_agent_application_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    applications: Annotated[
        AgentApplicationRepository,
        Depends(get_agent_application_repository),
    ],
    contributors: Annotated[
        ContributorRepository,
        Depends(get_contributor_repository),
    ],
) -> AgentApplicationService:
    return AgentApplicationService(session, applications, contributors)


def get_agent_score_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    contributors: Annotated[
        ContributorRepository,
        Depends(get_contributor_repository),
    ],
    rewards: Annotated[
        RewardSettingsRepository,
        Depends(get_reward_settings_repository),
    ],
) -> AgentScoreService:
    return AgentScoreService(session, contributors, rewards)


def get_submission_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubmissionRepository:
    return SubmissionRepository(session)


def get_submission_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    submissions: Annotated[SubmissionRepository, Depends(get_submission_repository)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    contributors: Annotated[
        ContributorRepository,
        Depends(get_contributor_repository),
    ],
    scores: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> SubmissionService:
    return SubmissionService(
        session, submissions, reference_data, contributors, scores
    )


@lru_cache
def get_password_service() -> PasswordService:
    return PasswordService()


@lru_cache
def get_jwt_service() -> JWTService:
    return JWTService(get_settings())


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    auth_sessions: Annotated[
        AuthSessionRepository,
        Depends(get_auth_session_repository),
    ],
    contributors: Annotated[
        ContributorRepository,
        Depends(get_contributor_repository),
    ],
    invite_tokens: Annotated[
        InviteTokenRepository,
        Depends(get_invite_token_repository),
    ],
    passwords: Annotated[PasswordService, Depends(get_password_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        session,
        users,
        auth_sessions,
        contributors,
        invite_tokens,
        passwords,
        jwt_service,
        settings,
    )


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _authentication_error()
    try:
        return await auth_service.authenticate_access_token(credentials.credentials)
    except InvalidAccessTokenError as error:
        raise _authentication_error() from error


RoleDependency = Callable[..., Awaitable[User]]


def require_roles(*allowed_roles: UserRole) -> RoleDependency:
    allowed = frozenset(allowed_roles)

    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


def _authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
