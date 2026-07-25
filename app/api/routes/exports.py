from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.dependencies import (
    get_current_subscriber,
    get_export_service,
    get_subscription_service,
    require_feature,
)
from app.models.auth import User
from app.models.enums import GateFeature
from app.services.exceptions import ExportQuotaExceededError, SubscriptionNotFoundError
from app.services.exports import ExportService
from app.services.subscriptions import SubscriptionContext, SubscriptionService

router = APIRouter(tags=["exports"])


@router.get("/exports/panel.csv")
async def export_panel_csv(
    export_service: Annotated[ExportService, Depends(get_export_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    current_user: Annotated[User, Depends(get_current_subscriber)],
    _context: Annotated[SubscriptionContext, Depends(require_feature(GateFeature.EXPORT))],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> Response:
    _ = _context
    try:
        await subscription_service.record_export(current_user.id)
    except ExportQuotaExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "tier_required", "message": "Daily export limit reached"}},
        ) from error
    except SubscriptionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "tier_required", "message": "Export not available"}},
        ) from error

    csv_body = await export_service.panel_csv(start=from_date, end=to_date)
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="waga-panel.csv"'},
    )
