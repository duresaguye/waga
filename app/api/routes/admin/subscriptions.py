from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_subscription_service, require_roles
from app.models.enums import PaymentStatus, UserRole
from app.schemas.subscriptions import (
    AdminSubscriptionResponse,
    AdminSubscriptionUpdate,
    EnterpriseEnquiryResponse,
    EnterpriseEnquiryStatusUpdate,
    PaymentResponse,
)
from app.services.exceptions import SubscriptionNotFoundError
from app.services.subscriptions import SubscriptionService

subscriptions_router = APIRouter(
    prefix="/subscriptions",
    tags=["admin-subscriptions"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)

enquiries_router = APIRouter(
    prefix="/enterprise-enquiries",
    tags=["admin-enterprise-enquiries"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))],
)


@subscriptions_router.get("", response_model=list[AdminSubscriptionResponse])
async def list_subscriptions(
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> list[AdminSubscriptionResponse]:
    rows = await service.list_subscriptions()
    results: list[AdminSubscriptionResponse] = []
    for user, subscription in rows:
        effective_tier = service.get_effective_tier(subscription)
        results.append(
            AdminSubscriptionResponse(
                user_id=user.id,
                email=user.email,
                full_name=user.display_name,
                organisation=subscription.organisation,
                tier=subscription.tier,
                effective_tier=effective_tier,
                status=subscription.status,
                billing_plan=subscription.billing_plan,
                trial_started_at=subscription.trial_started_at,
                trial_ends_at=subscription.trial_ends_at,
                activated_at=subscription.activated_at,
                cancelled_at=subscription.cancelled_at,
                created_at=subscription.created_at,
            )
        )
    return results


@subscriptions_router.patch("/{user_id}", response_model=AdminSubscriptionResponse)
async def update_subscription(
    user_id: UUID,
    body: AdminSubscriptionUpdate,
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> AdminSubscriptionResponse:
    try:
        subscription = await service.admin_update_subscription(
            user_id,
            tier=body.tier,
            status=body.status,
            billing_plan=body.billing_plan,
        )
    except SubscriptionNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription not found") from error

    rows = await service.list_subscriptions()
    user = next((row[0] for row in rows if row[0].id == user_id), None)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    effective_tier = service.get_effective_tier(subscription)
    return AdminSubscriptionResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.display_name,
        organisation=subscription.organisation,
        tier=subscription.tier,
        effective_tier=effective_tier,
        status=subscription.status,
        billing_plan=subscription.billing_plan,
        trial_started_at=subscription.trial_started_at,
        trial_ends_at=subscription.trial_ends_at,
        activated_at=subscription.activated_at,
        cancelled_at=subscription.cancelled_at,
        created_at=subscription.created_at,
    )


@subscriptions_router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    status_filter: Annotated[PaymentStatus | None, Query(alias="status")] = None,
) -> list[PaymentResponse]:
    payments = await service.list_payments(status=status_filter)
    return [PaymentResponse.model_validate(payment) for payment in payments]


@enquiries_router.get("", response_model=list[EnterpriseEnquiryResponse])
async def list_enterprise_enquiries(
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> list[EnterpriseEnquiryResponse]:
    enquiries = await service.list_enquiries()
    return [EnterpriseEnquiryResponse.model_validate(enquiry) for enquiry in enquiries]


@enquiries_router.patch("/{enquiry_id}", response_model=EnterpriseEnquiryResponse)
async def update_enterprise_enquiry(
    enquiry_id: UUID,
    body: EnterpriseEnquiryStatusUpdate,
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> EnterpriseEnquiryResponse:
    try:
        enquiry = await service.update_enquiry_status(enquiry_id, body.status)
    except SubscriptionNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Enquiry not found") from error
    return EnterpriseEnquiryResponse.model_validate(enquiry)
