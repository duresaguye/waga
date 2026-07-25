from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_admin_dashboard_service
from app.services.admin_dashboard import AdminDashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["admin-dashboard"],
)


@router.get("")
async def get_admin_dashboard(
    service: Annotated[AdminDashboardService, Depends(get_admin_dashboard_service)],
) -> dict:
    return await service.get_dashboard()
