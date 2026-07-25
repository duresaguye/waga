from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_agent_application_service, get_agent_score_service
from app.schemas.agents import (
    AgentActivateRequest,
    AgentActivateResponse,
    AgentRedeemResponse,
    AgentScoreResponse,
)
from app.schemas.applications import AgentApplicationCreate, AgentApplicationResponse
from app.services.agent_applications import AgentApplicationService
from app.services.agent_score import AgentScoreService
from app.services.exceptions import (
    AgentApplicationConflictError,
    AgentBannedError,
    AgentInviteInvalidError,
    AgentNotFoundError,
    AgentRedeemNotReadyError,
    AgentScoreError,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/applications",
    response_model=AgentApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_agent_application(
    body: AgentApplicationCreate,
    service: Annotated[AgentApplicationService, Depends(get_agent_application_service)],
) -> AgentApplicationResponse:
    """Public apply endpoint used by the Telegram bot."""
    try:
        application = await service.submit_application(
            telegram_id=body.telegram_id,
            telegram_username=body.telegram_username,
            full_name=body.full_name,
            phone_number=body.phone_number,
            city=body.city,
            subcity=body.subcity,
            preferred_market_code=body.preferred_market_code,
            visit_frequency=body.visit_frequency,
            languages=body.languages,
            notes=body.notes,
            consent_honest_reporting=body.consent_honest_reporting,
        )
    except AgentApplicationConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    except AgentScoreError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return AgentApplicationResponse.model_validate(application)


@router.post(
    "/activate",
    response_model=AgentActivateResponse,
    status_code=status.HTTP_200_OK,
)
async def activate_agent(
    body: AgentActivateRequest,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentActivateResponse:
    try:
        contributor = await service.activate_with_invite(
            telegram_id=body.telegram_id,
            invite_code=body.invite_code,
            display_name=body.display_name,
        )
    except AgentInviteInvalidError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except AgentBannedError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except AgentScoreError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    score = AgentScoreResponse.model_validate(await service.to_score_dict(contributor))
    return AgentActivateResponse(
        ok=True,
        message="Agent activated. You can submit market prices and earn redeemable score.",
        score=score,
    )


@router.get("/{telegram_id}/score", response_model=AgentScoreResponse)
async def get_agent_score(
    telegram_id: str,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentScoreResponse:
    try:
        contributor = await service.get_by_telegram_id(telegram_id)
    except AgentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return AgentScoreResponse.model_validate(await service.to_score_dict(contributor))


@router.post("/{telegram_id}/redeem", response_model=AgentRedeemResponse)
async def redeem_agent_score(
    telegram_id: str,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentRedeemResponse:
    try:
        contributor, points, birr_amount, request = await service.redeem(telegram_id)
    except AgentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except AgentBannedError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except AgentRedeemNotReadyError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    score = AgentScoreResponse.model_validate(await service.to_score_dict(contributor))
    return AgentRedeemResponse(
        ok=True,
        message=(
            f"Redeem request recorded: {points} points → "
            f"{birr_amount} {request.currency_code}. "
            "The Waga team will pay after verification."
        ),
        points_redeemed=points,
        birr_amount=birr_amount,
        currency_code=request.currency_code,
        score=score,
    )


@router.post("/{telegram_id}/pending", response_model=AgentScoreResponse)
async def record_pending_submit(
    telegram_id: str,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentScoreResponse:
    try:
        contributor = await service.record_pending_submit(telegram_id)
    except AgentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except AgentBannedError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    return AgentScoreResponse.model_validate(await service.to_score_dict(contributor))


@router.post("/{telegram_id}/review/accept", response_model=AgentScoreResponse)
async def accept_affects_score(
    telegram_id: str,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentScoreResponse:
    try:
        contributor = await service.apply_review(telegram_id, accepted=True)
    except AgentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return AgentScoreResponse.model_validate(await service.to_score_dict(contributor))


@router.post("/{telegram_id}/review/flag", response_model=AgentScoreResponse)
async def flag_affects_score(
    telegram_id: str,
    service: Annotated[AgentScoreService, Depends(get_agent_score_service)],
) -> AgentScoreResponse:
    try:
        contributor = await service.apply_review(telegram_id, accepted=False)
    except AgentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return AgentScoreResponse.model_validate(await service.to_score_dict(contributor))
