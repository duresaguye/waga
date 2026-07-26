from fastapi import APIRouter

from app.api.routes.admin.router import admin_router
from app.api.routes.affordability import router as affordability_router
from app.api.routes.agents import router as agents_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.auth import router as auth_router
from app.api.routes.briefs import router as briefs_router
from app.api.routes.business import router as business_router
from app.api.routes.copilot import router as copilot_router
from app.api.routes.coverage import router as coverage_router
from app.api.routes.exports import router as exports_router
from app.api.routes.health import router as health_router
from app.api.routes.heatmap import router as heatmap_router
from app.api.routes.prices import router as prices_router
from app.api.routes.research import router as research_router
from app.api.routes.submissions import router as submissions_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(agents_router)
api_router.include_router(submissions_router)
api_router.include_router(subscriptions_router)
api_router.include_router(webhooks_router)
api_router.include_router(prices_router)
api_router.include_router(coverage_router)
api_router.include_router(heatmap_router)
api_router.include_router(affordability_router)
api_router.include_router(copilot_router)
api_router.include_router(briefs_router)
api_router.include_router(alerts_router)
api_router.include_router(business_router)
api_router.include_router(research_router)
api_router.include_router(exports_router)
api_router.include_router(admin_router)
