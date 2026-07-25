from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db_session
from app.models.auth import User
from app.models.enums import GateFeature, UserRole, UserStatus
from app.repositories.agent_applications import AgentApplicationRepository
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.contributors import ContributorRepository
from app.repositories.index_values import IndexValueRepository
from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.repositories.reward_settings import RewardSettingsRepository
from app.repositories.submissions import SubmissionRepository
from app.repositories.subscription_plans import SubscriptionPlanRepository
from app.repositories.subscriptions import SubscriptionRepository
from app.repositories.users import UserRepository
from app.security import JWTService, PasswordService
from app.services.admin_dashboard import AdminDashboardService
from app.services.agent_applications import AgentApplicationService
from app.services.agent_score import AgentScoreService
from app.services.auth import AuthService
from app.services.chapa import ChapaPaymentService
from app.services.exceptions import InvalidAccessTokenError
from app.services.exports import ExportService
from app.services.heatmap import HeatmapService
from app.services.index_calculation import IndexCalculationService
from app.services.prices_read import PricesReadService
from app.services.reference_data import ReferenceDataService
from app.services.reviews import ReviewService
from app.services.submissions import SubmissionService
from app.services.subscription_plans import SubscriptionPlanService
from app.services.subscriptions import SubscriptionContext, SubscriptionService

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


def get_index_value_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IndexValueRepository:
    return IndexValueRepository(session)


def get_index_calculation_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    submissions: Annotated[SubmissionRepository, Depends(get_submission_repository)],
    index_values: Annotated[IndexValueRepository, Depends(get_index_value_repository)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IndexCalculationService:
    return IndexCalculationService(
        session,
        submissions,
        index_values,
        reference_data,
        settings,
    )


def get_prices_read_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    index_values: Annotated[IndexValueRepository, Depends(get_index_value_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PricesReadService:
    return PricesReadService(session, reference_data, index_values, settings)


def get_heatmap_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    index_values: Annotated[IndexValueRepository, Depends(get_index_value_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HeatmapService:
    return HeatmapService(session, reference_data, index_values, settings)


def get_export_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    index_values: Annotated[IndexValueRepository, Depends(get_index_value_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ExportService:
    return ExportService(session, reference_data, index_values, settings)


def get_affordability_service(
    prices: Annotated[PricesReadService, Depends(get_prices_read_service)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> "AffordabilityService":
    from app.services.affordability import AffordabilityService

    return AffordabilityService(prices, reference_data, settings)


def get_copilot_service(
    affordability: Annotated["AffordabilityService", Depends(get_affordability_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> "CopilotService":
    from app.services.copilot import CopilotService

    return CopilotService(affordability, settings)


def get_alerts_service(
    prices: Annotated[PricesReadService, Depends(get_prices_read_service)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    index_values: Annotated[IndexValueRepository, Depends(get_index_value_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> "AlertsService":
    from app.services.alerts import AlertsService

    return AlertsService(prices, reference_data, index_values, settings)


def get_business_service(
    prices: Annotated[PricesReadService, Depends(get_prices_read_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> "BusinessService":
    from app.services.business import BusinessService

    return BusinessService(prices, settings)


def get_research_service(
    prices: Annotated[PricesReadService, Depends(get_prices_read_service)],
    reference_data: Annotated[
        ReferenceDataRepository,
        Depends(get_reference_data_repository),
    ],
    index_values: Annotated[IndexValueRepository, Depends(get_index_value_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> "ResearchService":
    from app.services.research import ResearchService

    return ResearchService(prices, reference_data, index_values, settings)


def get_review_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    submissions: Annotated[SubmissionRepository, Depends(get_submission_repository)],
    scores: Annotated[AgentScoreService, Depends(get_agent_score_service)],
    index_calculation: Annotated[
        IndexCalculationService,
        Depends(get_index_calculation_service),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReviewService:
    return ReviewService(session, submissions, scores, index_calculation, settings)


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


def get_subscription_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionRepository:
    return SubscriptionRepository(session)


def get_admin_dashboard_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    applications: Annotated[
        AgentApplicationRepository,
        Depends(get_agent_application_repository),
    ],
    subscriptions: Annotated[
        SubscriptionRepository,
        Depends(get_subscription_repository),
    ],
    rewards: Annotated[
        RewardSettingsRepository,
        Depends(get_reward_settings_repository),
    ],
) -> AdminDashboardService:
    return AdminDashboardService(session, applications, subscriptions, rewards)


def get_subscription_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    subscriptions: Annotated[
        SubscriptionRepository,
        Depends(get_subscription_repository),
    ],
    auth_sessions: Annotated[
        AuthSessionRepository,
        Depends(get_auth_session_repository),
    ],
    passwords: Annotated[PasswordService, Depends(get_password_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SubscriptionService:
    return SubscriptionService(
        session,
        users,
        subscriptions,
        auth_sessions,
        passwords,
        jwt_service,
        settings,
    )


def get_subscription_plan_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionPlanRepository:
    return SubscriptionPlanRepository(session)


def get_subscription_plan_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    plans: Annotated[
        SubscriptionPlanRepository,
        Depends(get_subscription_plan_repository),
    ],
) -> SubscriptionPlanService:
    return SubscriptionPlanService(session, plans)


def get_chapa_payment_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    subscriptions: Annotated[
        SubscriptionRepository,
        Depends(get_subscription_repository),
    ],
    subscription_service: Annotated[
        SubscriptionService,
        Depends(get_subscription_service),
    ],
    plan_service: Annotated[
        SubscriptionPlanService,
        Depends(get_subscription_plan_service),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChapaPaymentService:
    return ChapaPaymentService(
        session,
        subscriptions,
        subscription_service,
        plan_service,
        settings,
    )


async def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        return await auth_service.authenticate_access_token(credentials.credentials)
    except InvalidAccessTokenError as error:
        raise _authentication_error() from error


async def get_subscription_context(
    optional_user: Annotated[User | None, Depends(get_optional_user)],
    subscription_service: Annotated[
        SubscriptionService,
        Depends(get_subscription_service),
    ],
) -> SubscriptionContext:
    return await subscription_service.get_context_for_user(optional_user)


async def get_current_subscriber(
    current_user: Annotated[User, Depends(get_current_user)],
    subscription_service: Annotated[
        SubscriptionService,
        Depends(get_subscription_service),
    ],
) -> User:
    if current_user.role != UserRole.SUBSCRIBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscriber account required",
        )
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )
    await subscription_service.ensure_subscription(current_user)
    return current_user


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


admin_role_dependency = require_roles(UserRole.ADMIN, UserRole.OPERATOR)


FeatureDependency = Callable[..., Awaitable[SubscriptionContext]]


def require_feature(feature: GateFeature) -> FeatureDependency:
    async def dependency(
        context: Annotated[SubscriptionContext, Depends(get_subscription_context)],
        subscription_service: Annotated[
            SubscriptionService,
            Depends(get_subscription_service),
        ],
        optional_user: Annotated[User | None, Depends(get_optional_user)],
    ) -> SubscriptionContext:
        exports_used = 0
        if optional_user is not None:
            exports_used = await subscription_service.exports_used_today(optional_user.id)
        access = subscription_service.can_access(
            context.subscription,
            feature,
            exports_used_today=exports_used,
        )
        if not access.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "tier_required",
                        "message": f"Feature '{feature.value}' requires a higher subscription tier",
                    }
                },
            )
        return context

    return dependency


def _authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "unauthorized",
                "message": "Invalid or expired access token",
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
