from fastapi import APIRouter

from app.api.routes.admin.reference_data import (
    router as admin_reference_data_router,
)

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_reference_data_router)
