from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_admin_dashboard_service, get_heatmap_service, get_current_user
from app.main import app
from app.models.auth import User
from app.models.enums import UserRole, UserStatus


class FakeHeatmapService:
    async def get_heatmap(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-heat-v1"},
            "data": {
                "metric": "pct_change_7d",
                "markets": [{"market_code": "merkato", "heat": 4.6, "band": "warm"}],
                "hottest_cell": {"market_code": "merkato", "commodity_code": "onion"},
            },
        }


class FakeAdminDashboardService:
    async def get_dashboard(self) -> dict:
        return {
            "stats": {
                "pending_agents": 1,
                "total_accounts": 3,
                "pending_redemptions": 2,
            },
            "analytics": {
                "mrr_estimate": 87,
                "conversion_rate": 33,
            },
            "badges": {
                "agents": 1,
                "accounts": 3,
                "enterprise": 1,
                "redemptions": 2,
            },
        }


@pytest.fixture
def admin_user() -> User:
    return User(
        id=uuid4(),
        email="admin@waga.com",
        password_hash="unused",
        display_name="Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        auth_version=1,
        failed_login_attempts=0,
        created_at=datetime(2026, 7, 25, tzinfo=UTC),
    )


@pytest.fixture
def client(admin_user: User):
    app.dependency_overrides[get_heatmap_service] = lambda: FakeHeatmapService()
    app.dependency_overrides[get_admin_dashboard_service] = lambda: FakeAdminDashboardService()
    app.dependency_overrides[get_current_user] = lambda: admin_user
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_heatmap_is_public() -> None:
    app.dependency_overrides[get_heatmap_service] = lambda: FakeHeatmapService()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as bare_client:
            response = await bare_client.get("/api/v1/heatmap")
        assert response.status_code == 200
        assert response.json()["data"]["metric"] == "pct_change_7d"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_dashboard_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["pending_agents"] == 1
    assert body["badges"]["redemptions"] == 2
