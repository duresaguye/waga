from fastapi import APIRouter

from app.api.routes.admin.router import admin_router
from app.api.routes.affordability import router as affordability_router
from app.api.routes.agents import router as agents_router
from app.api.routes.auth import router as auth_router
from app.api.routes.copilot import router as copilot_router
from app.api.routes.health import router as health_router
from app.api.routes.heatmap import router as heatmap_router
from app.api.routes.prices import router as prices_router
from app.api.routes.submissions import router as submissions_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(agents_router)
api_router.include_router(submissions_router)
api_router.include_router(prices_router)
api_router.include_router(affordability_router)
api_router.include_router(heatmap_router)
api_router.include_router(copilot_router)
api_router.include_router(admin_router)
