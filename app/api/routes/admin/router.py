from fastapi import APIRouter

from app.api.routes.admin.applications import (
    router as admin_applications_router,
)
from app.api.routes.admin.invites import router as admin_invites_router
from app.api.routes.admin.reference_data import (
    router as admin_reference_data_router,
)
from app.api.routes.admin.reviews import router as admin_reviews_router
from app.api.routes.admin.rewards import router as admin_rewards_router

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_reference_data_router)
admin_router.include_router(admin_rewards_router)
admin_router.include_router(admin_applications_router)
admin_router.include_router(admin_reviews_router)
admin_router.include_router(admin_invites_router)
