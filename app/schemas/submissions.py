from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreate(BaseModel):
    client_submission_id: UUID
    market_code: str = Field(min_length=1, max_length=64)
    commodity_code: str = Field(min_length=1, max_length=64)
    price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    unit: str = Field(min_length=1, max_length=32)
    external_contributor_id: str = Field(min_length=1, max_length=80)
    consent_version: str = Field(default="contributor-v1", min_length=1, max_length=64)
    input_mode: Literal["telegram", "rest"] = "telegram"
    source: Literal["user", "agent"] = "user"
    telegram_username: str | None = Field(default=None, max_length=64)
    market_label: str | None = Field(default=None, max_length=160)
    observed_at: datetime | None = None


class SubmissionScoreSnapshot(BaseModel):
    score: int
    status: str
    pending_count: int
    accepted_count: int
    flagged_count: int
    banned: bool
    ban_reason: str | None = None


class SubmissionCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_submission_id: UUID
    market_code: str
    commodity_code: str
    price: Decimal
    unit: str
    review_status: Literal["pending"] = "pending"
    market_label: str | None = None
    score: SubmissionScoreSnapshot
