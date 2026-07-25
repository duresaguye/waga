import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_chapa_payment_service
from app.services.chapa import ChapaPaymentService
from app.services.exceptions import (
    ChapaNotConfiguredError,
    ChapaWebhookInvalidError,
    PaymentNotFoundError,
)

router = APIRouter(prefix="/webhooks/chapa", tags=["webhooks"])


async def _handle_chapa_event(
    request: Request,
    chapa: Annotated[ChapaPaymentService, Depends(get_chapa_payment_service)],
) -> dict[str, str]:
    body = await request.body()
    signature = request.headers.get("x-chapa-signature") or request.headers.get(
        "chapa-signature"
    )
    try:
        chapa.verify_webhook_signature(body, signature)
    except ChapaNotConfiguredError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chapa webhook is not configured",
        ) from error
    except ChapaWebhookInvalidError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        ) from error

    content_type = request.headers.get("content-type", "")
    payload: dict[str, object]
    if "application/json" in content_type:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body") from error
        if not isinstance(parsed, dict):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload")
        payload = parsed
    else:
        form = await request.form()
        payload = dict(form)

    try:
        payment = await chapa.handle_webhook_payload(payload)
    except PaymentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Payment not found") from error
    except ChapaNotConfiguredError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chapa is not configured",
        ) from error

    return {"status": payment.status.value, "tx_ref": payment.tx_ref}


@router.post("/callback")
async def chapa_callback(
    request: Request,
    chapa: Annotated[ChapaPaymentService, Depends(get_chapa_payment_service)],
) -> dict[str, str]:
    return await _handle_chapa_event(request, chapa)


@router.post("")
async def chapa_webhook(
    request: Request,
    chapa: Annotated[ChapaPaymentService, Depends(get_chapa_payment_service)],
) -> dict[str, str]:
    return await _handle_chapa_event(request, chapa)
