from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRewardSettingsResponse(BaseModel):
    id: UUID
    birr_per_point: Decimal
    redeem_min_points: int
    currency_code: str
    is_active: bool
    example: str

    model_config = {"from_attributes": True}


class AgentRewardSettingsUpdate(BaseModel):
    birr_per_point: Decimal = Field(gt=0)
    redeem_min_points: int = Field(gt=0, le=1_000_000)
    currency_code: str = Field(default="ETB", min_length=3, max_length=8)


class AgentRedeemRequestResponse(BaseModel):
    id: UUID
    contributor_id: UUID
    telegram_id: str | None
    points_redeemed: int
    birr_per_point: Decimal
    birr_amount: Decimal
    currency_code: str
    status: str
    admin_note: str | None
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class AgentRedeemResolveRequest(BaseModel):
    status: str = Field(pattern="^(paid|rejected)$")
    admin_note: str | None = Field(default=None, max_length=255)
