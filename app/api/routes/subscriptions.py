from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_chapa_payment_service,
    get_current_subscriber,
    get_optional_user,
    get_subscription_context,
    get_subscription_plan_service,
    get_subscription_service,
)
from app.models.auth import User
from app.schemas.auth import TokenResponse
from app.schemas.subscription_plans import SubscriptionPlanResponse
from app.schemas.subscriptions import (
    AccessFeatureResult,
    AccessMatrixResponse,
    CheckoutRequest,
    CheckoutResponse,
    EnterpriseEnquiryRequest,
    EnterpriseEnquiryResponse,
    ExportRecordResponse,
    PaymentResponse,
    SubscriberRegisterRequest,
    SubscriptionResponse,
)
from app.services.chapa import ChapaPaymentService
from app.services.exceptions import (
    ChapaApiError,
    ChapaNotConfiguredError,
    EmailAlreadyRegisteredError,
    ExportQuotaExceededError,
    InvalidCredentialsError,
    PasswordPolicyError,
    PaymentNotFoundError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
)
from app.services.subscription_plans import SubscriptionPlanService
from app.services.subscriptions import SubscriptionContext, SubscriptionService
from app.services.api_errors import error_body

router = APIRouter(tags=["subscriptions"])


def _token_response(tokens) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
        expires_in=tokens.expires_in,
    )


def _subscription_response(
    service: SubscriptionService,
    context: SubscriptionContext,
    exports_used_today: int,
) -> SubscriptionResponse:
    subscription = context.subscription
    if context.user is None or subscription is None:
        raise SubscriptionNotFoundError

    effective_tier = context.effective_tier
    quota = service.export_quota(effective_tier)
    return SubscriptionResponse(
        user_id=context.user.id,
        email=context.user.email,
        full_name=context.user.display_name,
        organisation=subscription.organisation,
        tier=subscription.tier,
        effective_tier=effective_tier,
        api_contract_tier=service.api_contract_tier(effective_tier),
        status=subscription.status,
        billing_plan=subscription.billing_plan,
        trial_started_at=subscription.trial_started_at,
        trial_ends_at=subscription.trial_ends_at,
        activated_at=subscription.activated_at,
        cancelled_at=subscription.cancelled_at,
        language=subscription.language,
        history_depth_days=service.history_depth_days(subscription),
        exports_used_today=exports_used_today,
        export_quota=quota,
        created_at=subscription.created_at,
    )


@router.post(
    "/auth/subscriber/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Register a consumer (subscriber) account",
)
async def register_subscriber(
    request: SubscriberRegisterRequest,
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> TokenResponse:
    try:
        tokens = await service.register_subscriber(
            str(request.email),
            request.password,
            request.full_name,
            request.organisation,
            request.language,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "email_already_registered",
                    "message": "Email is already registered with an active subscription",
                }
            },
        ) from error
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except PasswordPolicyError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    return _token_response(tokens)


@router.get("/subscriptions/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: Annotated[User, Depends(get_current_subscriber)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> SubscriptionResponse:
    context = await service.get_context_for_user(current_user)
    if context.subscription is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    exports_used = await service.exports_used_today(current_user.id)
    return _subscription_response(service, context, exports_used)


@router.get("/subscriptions/access", response_model=AccessMatrixResponse)
async def get_access_matrix(
    context: Annotated[SubscriptionContext, Depends(get_subscription_context)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    optional_user: Annotated[User | None, Depends(get_optional_user)],
) -> AccessMatrixResponse:
    exports_used = 0
    if optional_user is not None:
        exports_used = await service.exports_used_today(optional_user.id)
    matrix = service.access_matrix(context.subscription, exports_used)
    return AccessMatrixResponse(
        effective_tier=context.effective_tier,
        api_contract_tier=service.api_contract_tier(context.effective_tier),
        features={
            feature: AccessFeatureResult(allowed=result.allowed, reason=result.reason)
            for feature, result in matrix.items()
        },
    )


@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def list_public_plans(
    service: Annotated[SubscriptionPlanService, Depends(get_subscription_plan_service)],
) -> list[SubscriptionPlanResponse]:
    plans = await service.list_plans(active_only=True, public_only=True)
    return [SubscriptionPlanResponse.model_validate(plan) for plan in plans]


@router.post("/subscriptions/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    current_user: Annotated[User, Depends(get_current_subscriber)],
    chapa: Annotated[ChapaPaymentService, Depends(get_chapa_payment_service)],
) -> CheckoutResponse:
    try:
        payment = await chapa.create_checkout(
            current_user,
            plan_id=request.plan_id,
            billing_plan=request.billing_plan,
        )
    except SubscriptionNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription not found") from error
    except PlanNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ChapaNotConfiguredError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_body(
                "chapa_not_configured",
                "Chapa payment is not configured. Set WAGA_CHAPA_TEST_SECRET_KEY in your environment.",
            ),
        ) from error
    except ChapaApiError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail=error_body("chapa_api_error", str(error)),
        ) from error
    if payment.checkout_url is None:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Chapa did not return a checkout URL",
        )
    return CheckoutResponse(
        payment_id=payment.id,
        tx_ref=payment.tx_ref,
        checkout_url=payment.checkout_url,
        amount_etb=payment.amount_etb,
        billing_plan=payment.billing_plan,
        status=payment.status,
    )


@router.get("/subscriptions/checkout/{payment_id}", response_model=PaymentResponse)
async def get_checkout_status(
    payment_id: UUID,
    current_user: Annotated[User, Depends(get_current_subscriber)],
    chapa: Annotated[ChapaPaymentService, Depends(get_chapa_payment_service)],
) -> PaymentResponse:
    try:
        payment = await chapa.get_checkout_status(current_user, payment_id)
    except PaymentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Payment not found") from error
    except ChapaNotConfiguredError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_body(
                "chapa_not_configured",
                "Chapa payment is not configured. Set WAGA_CHAPA_TEST_SECRET_KEY in your environment.",
            ),
        ) from error
    except ChapaApiError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail=error_body("chapa_api_error", str(error)),
        ) from error
    return PaymentResponse.model_validate(payment)


@router.post("/subscriptions/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    context: Annotated[SubscriptionContext, Depends(get_subscription_context)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    current_user: Annotated[User, Depends(get_current_subscriber)],
) -> SubscriptionResponse:
    try:
        await service.cancel_subscription(current_user.id)
    except SubscriptionNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription not found") from error
    refreshed = await service.get_context_for_user(current_user)
    exports_used = await service.exports_used_today(current_user.id)
    return _subscription_response(service, refreshed, exports_used)


@router.post(
    "/subscriptions/enterprise-enquiries",
    response_model=EnterpriseEnquiryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_enterprise_enquiry(
    request: EnterpriseEnquiryRequest,
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> EnterpriseEnquiryResponse:
    enquiry = await service.submit_enterprise_enquiry(
        request.name,
        request.organisation,
        str(request.email),
        request.use_case,
        request.update_frequency,
    )
    return EnterpriseEnquiryResponse.model_validate(enquiry)


@router.post("/subscriptions/exports/record", response_model=ExportRecordResponse)
async def record_export(
    context: Annotated[SubscriptionContext, Depends(get_subscription_context)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    current_user: Annotated[User, Depends(get_current_subscriber)],
) -> ExportRecordResponse:
    try:
        used = await service.record_export(current_user.id)
    except ExportQuotaExceededError as error:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"code": "tier_required", "message": "Daily export limit reached"},
        ) from error
    except SubscriptionNotFoundError as error:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"code": "tier_required", "message": "Export not available on current tier"},
        ) from error
    quota = service.export_quota(context.effective_tier)
    return ExportRecordResponse(
        exports_used_today=used,
        export_quota=quota,
    )
