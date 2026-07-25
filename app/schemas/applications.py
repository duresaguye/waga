from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AgentApplicationCreate(BaseModel):
    telegram_id: str = Field(min_length=1, max_length=64)
    telegram_username: str | None = Field(default=None, max_length=64)
    full_name: str = Field(min_length=2, max_length=120)
    phone_number: str = Field(min_length=8, max_length=32)
    city: str = Field(default="Addis Ababa", min_length=2, max_length=80)
    subcity: str | None = Field(default=None, max_length=80)
    preferred_market_code: str = Field(min_length=2, max_length=64)
    visit_frequency: str = Field(min_length=2, max_length=64)
    languages: str | None = Field(default=None, max_length=120)
    notes: str | None = None
    consent_honest_reporting: bool = True


class AgentApplicationResponse(BaseModel):
    id: UUID
    telegram_id: str
    telegram_username: str | None
    full_name: str
    phone_number: str
    city: str
    subcity: str | None
    preferred_market_code: str
    visit_frequency: str
    languages: str | None
    notes: str | None
    consent_honest_reporting: bool
    status: str
    review_note: str | None
    created_at: datetime
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class AgentApplicationRejectRequest(BaseModel):
    review_note: str | None = Field(default=None, max_length=255)
