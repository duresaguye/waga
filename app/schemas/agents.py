from decimal import Decimal

from pydantic import BaseModel, Field


class AgentActivateRequest(BaseModel):
    telegram_id: str = Field(min_length=1, max_length=64)
    invite_code: str = Field(min_length=1, max_length=64)
    display_name: str | None = Field(default=None, max_length=120)


class AgentScoreResponse(BaseModel):
    telegram_id: str
    is_agent: bool
    score: int
    status: str
    pending_count: int
    accepted_count: int
    flagged_count: int
    redeemed_total: int
    banned: bool
    ban_reason: str | None
    can_redeem: bool
    redeem_threshold: int
    birr_per_point: Decimal
    estimated_birr: Decimal
    currency_code: str


class AgentRedeemResponse(BaseModel):
    ok: bool
    message: str
    points_redeemed: int
    birr_amount: Decimal
    currency_code: str
    score: AgentScoreResponse


class AgentActivateResponse(BaseModel):
    ok: bool
    message: str
    score: AgentScoreResponse
