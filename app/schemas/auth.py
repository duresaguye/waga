from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole, UserStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)
    display_name: str | None = Field(default=None, max_length=160)
    role: UserRole = UserRole.CONTRIBUTOR

    @field_validator("role")
    @classmethod
    def role_must_be_contributor(cls, value: UserRole) -> UserRole:
        if value != UserRole.CONTRIBUTOR:
            raise ValueError("Public registration is only available for contributor accounts")
        return value

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=1, max_length=1024)


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: UserRole
    display_name: str | None = Field(default=None, max_length=160)

    @field_validator("role")
    @classmethod
    def role_must_be_staff(cls, value: UserRole) -> UserRole:
        if value not in (UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER):
            raise ValueError("Invites are only for admin, operator, or viewer roles")
        return value

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class InviteUserResponse(BaseModel):
    email: EmailStr
    role: UserRole
    invite_token: str
    expires_in_hours: int = 24


class InviteAcceptRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    password: str = Field(min_length=1, max_length=1024)
    confirm_password: str = Field(min_length=1, max_length=1024)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    display_name: str | None
    role: UserRole
    status: UserStatus
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
