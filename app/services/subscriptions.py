from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.auth import AuthSession, User
from app.models.enums import (
    BillingPlan,
    DataTier,
    EnterpriseEnquiryStatus,
    GateFeature,
    PaymentStatus,
    SubscriberLanguage,
    SubscriptionStatus,
    UpdateFrequency,
    UserRole,
    UserStatus,
)
from app.models.subscriptions import EnterpriseEnquiry, Subscription, SubscriptionUsage
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.subscriptions import SubscriptionRepository
from app.repositories.users import UserRepository
from app.security import JWTService, PasswordService
from app.services.auth import AuthService, IssuedTokens, utc_now
from app.services.exceptions import (
    EmailAlreadyRegisteredError,
    ExportQuotaExceededError,
    InvalidCredentialsError,
    PasswordPolicyError,
    SubscriptionNotFoundError,
)

ENTERPRISE_ONLY: frozenset[GateFeature] = frozenset({GateFeature.API, GateFeature.BASKET})
PRO_SURFACES: frozenset[GateFeature] = frozenset(
    {
        GateFeature.HISTORY,
        GateFeature.SOURCE,
        GateFeature.CONFIDENCE,
        GateFeature.COMPARISON,
        GateFeature.MAP,
    }
)


@dataclass(frozen=True)
class AccessResult:
    allowed: bool
    reason: str  # ok | paywall | upgrade | limit


@dataclass(frozen=True)
class SubscriptionContext:
    user: User | None
    subscription: Subscription | None
    effective_tier: DataTier


class SubscriptionService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        subscriptions: SubscriptionRepository,
        auth_sessions: AuthSessionRepository,
        passwords: PasswordService,
        jwt_service: JWTService,
        settings: Settings,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._session = session
        self._users = users
        self._subscriptions = subscriptions
        self._auth_sessions = auth_sessions
        self._passwords = passwords
        self._jwt = jwt_service
        self._settings = settings
        self._clock = clock

    async def register_subscriber(
        self,
        email: str,
        password: str,
        full_name: str,
        organisation: str | None = None,
        language: SubscriberLanguage = SubscriberLanguage.EN,
    ) -> IssuedTokens:
        normalized_email = email.strip().lower()
        self._validate_password(password)

        existing = await self._users.get_by_email(normalized_email, for_update=True)
        if existing is not None:
            if not await self._passwords.verify(password, existing.password_hash):
                await self._session.rollback()
                raise InvalidCredentialsError
            existing_subscription = await self._subscriptions.get_subscription_by_user_id(
                existing.id,
            )
            if existing_subscription is not None:
                await self._session.rollback()
                raise EmailAlreadyRegisteredError
            if full_name.strip() and not existing.display_name:
                existing.display_name = full_name.strip()
            subscription = self._new_trial_subscription(
                existing.id,
                organisation,
                language,
            )
            self._subscriptions.add_subscription(subscription)
            refresh_token, auth_session = self._new_auth_session(existing.id)
            self._auth_sessions.add(auth_session)
            try:
                await self._session.commit()
            except IntegrityError as error:
                await self._session.rollback()
                raise EmailAlreadyRegisteredError from error
            return self._issued_tokens(existing, refresh_token)

        now = self._clock()
        user_id = uuid4()
        user = User(
            id=user_id,
            email=normalized_email,
            password_hash=await self._passwords.hash(password),
            display_name=full_name.strip(),
            role=UserRole.SUBSCRIBER,
            status=UserStatus.ACTIVE,
            auth_version=1,
            failed_login_attempts=0,
        )
        subscription = self._new_trial_subscription(
            user_id,
            organisation,
            language,
            now=now,
        )
        self._users.add(user)
        self._subscriptions.add_subscription(subscription)
        await self._session.flush()

        refresh_token, auth_session = self._new_auth_session(user_id)
        self._auth_sessions.add(auth_session)

        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError from error

        return self._issued_tokens(user, refresh_token)

    async def ensure_subscription(
        self,
        user: User,
        *,
        organisation: str | None = None,
        language: SubscriberLanguage = SubscriberLanguage.EN,
    ) -> Subscription:
        subscription = await self._subscriptions.get_subscription_by_user_id(
            user.id,
            for_update=True,
        )
        if subscription is not None:
            await self._session.commit()
            return subscription

        subscription = self._new_trial_subscription(
            user.id,
            organisation,
            language,
        )
        self._subscriptions.add_subscription(subscription)
        await self._session.commit()
        return subscription

    def _new_trial_subscription(
        self,
        user_id: UUID,
        organisation: str | None,
        language: SubscriberLanguage,
        *,
        now: datetime | None = None,
    ) -> Subscription:
        clock = now or self._clock()
        today = clock.date()
        trial_ends = today + timedelta(days=self._settings.trial_days)
        return Subscription(
            id=uuid4(),
            user_id=user_id,
            organisation=organisation.strip() if organisation else None,
            tier=DataTier.PROFESSIONAL,
            status=SubscriptionStatus.TRIAL,
            billing_plan=BillingPlan.MONTHLY,
            trial_started_at=today,
            trial_ends_at=trial_ends,
            language=language,
        )

    async def get_context_for_user(self, user: User | None) -> SubscriptionContext:
        if user is None:
            return SubscriptionContext(user=None, subscription=None, effective_tier=DataTier.PUBLIC)

        subscription = await self._subscriptions.get_subscription_by_user_id(
            user.id,
            for_update=True,
        )
        if subscription is None:
            await self._session.rollback()
            return SubscriptionContext(user=user, subscription=None, effective_tier=DataTier.PUBLIC)

        await self._apply_lazy_expiry(subscription)
        effective_tier = self.get_effective_tier(subscription)
        await self._session.commit()
        return SubscriptionContext(
            user=user,
            subscription=subscription,
            effective_tier=effective_tier,
        )

    async def _apply_lazy_expiry(self, subscription: Subscription) -> None:
        if subscription.status != SubscriptionStatus.TRIAL:
            return
        if subscription.trial_ends_at is None:
            return
        if subscription.trial_ends_at >= self._clock().date():
            return
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.updated_at = self._clock()

    def get_effective_tier(self, subscription: Subscription | None) -> DataTier:
        if subscription is None:
            return DataTier.PUBLIC
        if subscription.status not in (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE):
            return DataTier.PUBLIC
        if (
            subscription.status == SubscriptionStatus.TRIAL
            and subscription.trial_ends_at is not None
            and subscription.trial_ends_at < self._clock().date()
        ):
            return DataTier.PUBLIC
        return subscription.tier

    @staticmethod
    def api_contract_tier(data_tier: DataTier) -> str:
        if data_tier == DataTier.ENTERPRISE:
            return "research"
        if data_tier == DataTier.PROFESSIONAL:
            return "full"
        return "public"

    def can_access(
        self,
        subscription: Subscription | None,
        feature: GateFeature,
        *,
        exports_used_today: int = 0,
    ) -> AccessResult:
        tier = self.get_effective_tier(subscription)

        if feature in ENTERPRISE_ONLY:
            if tier == DataTier.ENTERPRISE:
                return AccessResult(True, "ok")
            return AccessResult(
                False,
                "paywall" if tier == DataTier.PUBLIC else "upgrade",
            )

        if feature in PRO_SURFACES:
            if tier == DataTier.PUBLIC:
                return AccessResult(False, "paywall")
            return AccessResult(True, "ok")

        if feature == GateFeature.EXPORT:
            if tier == DataTier.PUBLIC:
                return AccessResult(False, "paywall")
            quota = self.export_quota(tier)
            if quota is not None and exports_used_today >= quota:
                return AccessResult(False, "limit")
            return AccessResult(True, "ok")

        return AccessResult(True, "ok")

    def history_depth_days(self, subscription: Subscription | None) -> int | None:
        tier = self.get_effective_tier(subscription)
        if tier == DataTier.PUBLIC:
            return 0
        if tier == DataTier.ENTERPRISE:
            return None
        if subscription is None or subscription.billing_plan == BillingPlan.ANNUAL:
            return self._settings.history_days_annual
        return self._settings.history_days_monthly

    def export_quota(self, tier: DataTier) -> int | None:
        if tier == DataTier.ENTERPRISE:
            return None
        if tier == DataTier.PROFESSIONAL:
            return self._settings.pro_exports_per_day
        return 0

    async def exports_used_today(self, user_id: UUID) -> int:
        usage = await self._subscriptions.get_usage_for_date(user_id, self._clock().date())
        return usage.exports_count if usage is not None else 0

    async def record_export(self, user_id: UUID) -> int:
        subscription = await self._subscriptions.get_subscription_by_user_id(
            user_id,
            for_update=True,
        )
        if subscription is None:
            await self._session.rollback()
            raise SubscriptionNotFoundError

        await self._apply_lazy_expiry(subscription)
        used = await self.exports_used_today(user_id)
        access = self.can_access(subscription, GateFeature.EXPORT, exports_used_today=used)
        if not access.allowed:
            await self._session.rollback()
            if access.reason == "limit":
                raise ExportQuotaExceededError
            raise SubscriptionNotFoundError

        today = self._clock().date()
        usage = await self._subscriptions.get_usage_for_date(user_id, today, for_update=True)
        if usage is None:
            usage = SubscriptionUsage(
                id=uuid4(),
                user_id=user_id,
                usage_date=today,
                exports_count=1,
            )
            self._subscriptions.add_usage(usage)
        else:
            usage.exports_count += 1

        await self._session.commit()
        return usage.exports_count

    async def activate_subscription(
        self,
        user_id: UUID,
        billing_plan: BillingPlan,
        *,
        plan_id: UUID | None = None,
        tier: DataTier | None = None,
    ) -> Subscription:
        subscription = await self._subscriptions.get_subscription_by_user_id(
            user_id,
            for_update=True,
        )
        if subscription is None:
            await self._session.rollback()
            raise SubscriptionNotFoundError

        now = self._clock()
        subscription.tier = tier or DataTier.PROFESSIONAL
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.billing_plan = billing_plan
        subscription.plan_id = plan_id
        subscription.activated_at = now
        subscription.cancelled_at = None
        subscription.updated_at = now
        await self._session.commit()
        return subscription

    async def cancel_subscription(self, user_id: UUID) -> Subscription:
        subscription = await self._subscriptions.get_subscription_by_user_id(
            user_id,
            for_update=True,
        )
        if subscription is None:
            await self._session.rollback()
            raise SubscriptionNotFoundError

        now = self._clock()
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = now
        subscription.updated_at = now
        await self._session.commit()
        return subscription

    async def admin_update_subscription(
        self,
        user_id: UUID,
        *,
        tier: DataTier | None = None,
        status: SubscriptionStatus | None = None,
        billing_plan: BillingPlan | None = None,
    ) -> Subscription:
        subscription = await self._subscriptions.get_subscription_by_user_id(
            user_id,
            for_update=True,
        )
        if subscription is None:
            await self._session.rollback()
            raise SubscriptionNotFoundError

        now = self._clock()
        if tier is not None:
            subscription.tier = tier
        if status is not None:
            subscription.status = status
            if status == SubscriptionStatus.ACTIVE and subscription.activated_at is None:
                subscription.activated_at = now
            if status == SubscriptionStatus.CANCELLED:
                subscription.cancelled_at = now
        if billing_plan is not None:
            subscription.billing_plan = billing_plan
        subscription.updated_at = now
        await self._session.commit()
        return subscription

    async def submit_enterprise_enquiry(
        self,
        name: str,
        organisation: str,
        email: str,
        use_case: str,
        update_frequency: UpdateFrequency,
    ) -> EnterpriseEnquiry:
        enquiry = EnterpriseEnquiry(
            id=uuid4(),
            name=name.strip(),
            organisation=organisation.strip(),
            email=email.strip(),
            use_case=use_case.strip(),
            update_frequency=update_frequency,
            status=EnterpriseEnquiryStatus.NEW,
        )
        self._subscriptions.add_enquiry(enquiry)
        await self._session.commit()
        return enquiry

    async def update_enquiry_status(
        self,
        enquiry_id: UUID,
        status: EnterpriseEnquiryStatus,
    ) -> EnterpriseEnquiry:
        enquiry = await self._subscriptions.get_enquiry_by_id(enquiry_id, for_update=True)
        if enquiry is None:
            await self._session.rollback()
            raise SubscriptionNotFoundError
        enquiry.status = status
        enquiry.updated_at = self._clock()
        await self._session.commit()
        return enquiry

    async def list_subscriptions(self) -> list[tuple[User, Subscription]]:
        return await self._subscriptions.list_subscriptions()

    async def list_payments(self, *, status: PaymentStatus | None = None) -> list:
        return await self._subscriptions.list_payments(status=status)

    async def list_enquiries(self) -> list[EnterpriseEnquiry]:
        return await self._subscriptions.list_enquiries()

    def access_matrix(
        self,
        subscription: Subscription | None,
        exports_used_today: int,
    ) -> dict[str, AccessResult]:
        return {
            feature.value: self.can_access(
                subscription,
                feature,
                exports_used_today=exports_used_today,
            )
            for feature in GateFeature
        }

    def amount_for_plan(self, billing_plan: BillingPlan) -> int:
        if billing_plan == BillingPlan.ANNUAL:
            return self._settings.pro_annual_etb
        return self._settings.pro_monthly_etb

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

    def _new_auth_session(self, user_id: UUID) -> tuple[str, AuthSession]:
        now = self._clock()
        refresh_token = token_urlsafe(48)
        auth_session = AuthSession(
            id=uuid4(),
            user_id=user_id,
            refresh_token_hash=AuthService.hash_refresh_token(refresh_token),
            session_family_id=uuid4(),
            expires_at=now + timedelta(days=self._settings.refresh_token_days),
        )
        return refresh_token, auth_session

    def _issued_tokens(self, user: User, refresh_token: str) -> IssuedTokens:
        return IssuedTokens(
            access_token=self._jwt.create_access_token(user, self._clock()),
            refresh_token=refresh_token,
            expires_in=self._jwt.expires_in_seconds,
        )
