from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentActivateRequest(BaseModel):
    telegram_id: str = Field(min_length=1, max_length=64)
    invite_code: str = Field(min_length=1, max_length=64)
    display_name: str | None = Field(default=None, max_length=120)


class AgentInviteCreateRequest(BaseModel):
    """max_uses=1 → one person only; 0 → unlimited."""

    max_uses: int = Field(default=1, ge=0, le=10_000)


class AgentInviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    is_active: bool
    max_uses: int
    uses_count: int
    created_at: datetime
    telegram_hint: str

    @classmethod
    def from_invite(cls, invite: object) -> "AgentInviteResponse":
        code = str(getattr(invite, "code"))
        return cls(
            id=getattr(invite, "id"),
            code=code,
            is_active=bool(getattr(invite, "is_active")),
            max_uses=int(getattr(invite, "max_uses")),
            uses_count=int(getattr(invite, "uses_count")),
            created_at=getattr(invite, "created_at"),
            telegram_hint=f"/agent {code}",
        )


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
