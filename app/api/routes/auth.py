from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_auth_service, get_current_user, require_roles
from app.models.auth import User
from app.models.enums import UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    InviteAcceptRequest,
    InviteUserRequest,
    InviteUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService, IssuedTokens
from app.services.exceptions import (
    CurrentPasswordInvalidError,
    EmailAlreadyRegisteredError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InviteTokenAlreadyUsedError,
    InviteTokenExpiredError,
    InviteTokenNotFoundError,
    PasswordPolicyError,
    PasswordReuseError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        tokens = await auth_service.register(
            str(request.email),
            request.password,
            request.display_name,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from error
    except PasswordPolicyError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    return _token_response(tokens)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        tokens = await auth_service.login(str(request.email), request.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return _token_response(tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        tokens = await auth_service.refresh(request.refresh_token)
    except InvalidRefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from error
    return _token_response(tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    await auth_service.logout(request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    try:
        await auth_service.logout_all(current_user.id)
    except InvalidAccessTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.post("/change-password", response_model=TokenResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        tokens = await auth_service.change_password(
            current_user.id,
            request.current_password,
            request.new_password,
        )
    except CurrentPasswordInvalidError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        ) from error
    except PasswordReuseError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        ) from error
    except PasswordPolicyError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except InvalidAccessTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return _token_response(tokens)


@router.post(
    "/invite",
    response_model=InviteUserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def invite_user(
    request: InviteUserRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> InviteUserResponse:
    try:
        raw_token = await auth_service.invite_user(
            str(request.email),
            request.role,
            request.display_name,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from error
    return InviteUserResponse(
        email=request.email,
        role=request.role,
        invite_token=raw_token,
    )


@router.post("/invite/accept", response_model=TokenResponse)
async def accept_invite(
    request: InviteAcceptRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        tokens = await auth_service.accept_invite(request.token, request.password)
    except InviteTokenNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite token",
        ) from error
    except InviteTokenExpiredError as error:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invite link has expired. Contact your administrator.",
        ) from error
    except InviteTokenAlreadyUsedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invite link has already been used",
        ) from error
    except PasswordPolicyError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    return _token_response(tokens)


def _token_response(tokens: IssuedTokens) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
