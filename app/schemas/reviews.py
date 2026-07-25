from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewFlagRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    reason_code: str | None = Field(default=None, max_length=64)


class ReviewAcceptRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class PendingReviewItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: UUID
    client_submission_id: UUID
    received_at: datetime
    observed_at: datetime | None = None
    market_code: str
    market_name_en: str
    market_label: str | None = None
    commodity_code: str
    commodity_name_en: str
    price: Decimal
    unit: str | None = None
    review_status: Literal["pending", "accepted", "flagged"]
    telegram_id: str | None = None
    agent_score: int | None = None
    ai_verdict: Literal["accept", "hold", "flag"] | None = None
    ai_confidence: Literal["high", "medium", "low"] | None = None
    ai_reason: str | None = None
    ai_model: str | None = None
    ai_checked_at: datetime | None = None
    comparison_facts: dict[str, Any] | None = None
