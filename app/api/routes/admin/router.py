from fastapi import APIRouter, Depends

from app.api.routes.admin.dashboard import router as admin_dashboard_router
from app.api.routes.admin.applications import (
    router as admin_applications_router,
)
from app.api.routes.admin.invites import router as admin_invites_router
from app.api.routes.admin.reference_data import (
    router as admin_reference_data_router,
)
from app.api.routes.admin.reviews import router as admin_reviews_router
from app.api.routes.admin.rewards import router as admin_rewards_router
from app.api.routes.admin.plans import router as admin_plans_router
from app.api.routes.admin.subscriptions import (
    enquiries_router as admin_enquiries_router,
    subscriptions_router as admin_subscriptions_router,
)
from app.dependencies import admin_role_dependency

admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(admin_role_dependency)],
)
admin_router.include_router(admin_dashboard_router)
admin_router.include_router(admin_reference_data_router)
admin_router.include_router(admin_rewards_router)
admin_router.include_router(admin_applications_router)
admin_router.include_router(admin_reviews_router)
admin_router.include_router(admin_subscriptions_router)
admin_router.include_router(admin_enquiries_router)
admin_router.include_router(admin_plans_router)
admin_router.include_router(admin_invites_router)
