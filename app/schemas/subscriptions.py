from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.enums import (
    BillingPlan,
    DataTier,
    EnterpriseEnquiryStatus,
    PaymentStatus,
    SubscriberLanguage,
    SubscriptionStatus,
    UpdateFrequency,
)


class SubscriberRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)
    full_name: str = Field(min_length=1, max_length=160)
    organisation: str | None = Field(default=None, max_length=160)
    language: SubscriberLanguage = SubscriberLanguage.EN

    @field_validator("full_name", "organisation", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr
    full_name: str | None
    organisation: str | None
    tier: DataTier
    effective_tier: DataTier
    api_contract_tier: str
    status: SubscriptionStatus
    billing_plan: BillingPlan | None
    trial_started_at: date | None
    trial_ends_at: date | None
    activated_at: datetime | None
    cancelled_at: datetime | None
    language: SubscriberLanguage
    history_depth_days: int | None
    exports_used_today: int
    export_quota: int | None
    created_at: datetime


class AccessFeatureResult(BaseModel):
    allowed: bool
    reason: str


class AccessMatrixResponse(BaseModel):
    effective_tier: DataTier
    api_contract_tier: str
    features: dict[str, AccessFeatureResult]


class CheckoutRequest(BaseModel):
    plan_id: UUID | None = None
    billing_plan: BillingPlan | None = None

    @model_validator(mode="after")
    def require_plan_selector(self) -> "CheckoutRequest":
        if self.plan_id is None and self.billing_plan is None:
            raise ValueError("Either plan_id or billing_plan is required")
        return self


class CheckoutResponse(BaseModel):
    payment_id: UUID
    tx_ref: str
    checkout_url: str
    amount_etb: Decimal
    billing_plan: BillingPlan
    status: PaymentStatus


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    amount_etb: Decimal
    billing_plan: BillingPlan
    status: PaymentStatus
    tx_ref: str
    chapa_ref_id: str | None
    checkout_url: str | None
    failure_reason: str | None
    confirmed_at: datetime | None
    created_at: datetime


class EnterpriseEnquiryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    organisation: str = Field(min_length=1, max_length=160)
    email: EmailStr
    use_case: str = Field(min_length=1, max_length=5000)
    update_frequency: UpdateFrequency


class EnterpriseEnquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    organisation: str
    email: EmailStr
    use_case: str
    update_frequency: UpdateFrequency
    status: EnterpriseEnquiryStatus
    created_at: datetime
    updated_at: datetime


class AdminSubscriptionResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str | None
    organisation: str | None
    tier: DataTier
    effective_tier: DataTier
    status: SubscriptionStatus
    billing_plan: BillingPlan | None
    trial_started_at: date | None
    trial_ends_at: date | None
    activated_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime


class AdminSubscriptionUpdate(BaseModel):
    tier: DataTier | None = None
    status: SubscriptionStatus | None = None
    billing_plan: BillingPlan | None = None


class EnterpriseEnquiryStatusUpdate(BaseModel):
    status: EnterpriseEnquiryStatus


class ExportRecordResponse(BaseModel):
    exports_used_today: int
    export_quota: int | None
