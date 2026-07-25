from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import BillingPlan, DataTier


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    tier: DataTier
    billing_plan: BillingPlan | None
    name_en: str
    name_am: str
    description_en: str | None
    description_am: str | None
    amount_etb: Decimal
    trial_days: int | None
    exports_per_day: int | None
    history_days: int | None
    is_active: bool
    is_public: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class SubscriptionPlanCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    tier: DataTier
    billing_plan: BillingPlan | None = None
    name_en: str = Field(min_length=1, max_length=160)
    name_am: str = Field(min_length=1, max_length=160)
    description_en: str | None = None
    description_am: str | None = None
    amount_etb: Decimal = Field(gt=0)
    trial_days: int | None = Field(default=None, ge=0)
    exports_per_day: int | None = Field(default=None, ge=0)
    history_days: int | None = Field(default=None, ge=0)
    is_active: bool = True
    is_public: bool = True
    sort_order: int = 0

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class SubscriptionPlanUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    tier: DataTier | None = None
    billing_plan: BillingPlan | None = None
    name_en: str | None = Field(default=None, min_length=1, max_length=160)
    name_am: str | None = Field(default=None, min_length=1, max_length=160)
    description_en: str | None = None
    description_am: str | None = None
    amount_etb: Decimal | None = Field(default=None, gt=0)
    trial_days: int | None = Field(default=None, ge=0)
    exports_per_day: int | None = Field(default=None, ge=0)
    history_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    is_public: bool | None = None
    sort_order: int | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value
