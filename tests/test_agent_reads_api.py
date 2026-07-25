from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_agent_application_repository, get_reward_settings_repository
from app.main import app
from app.models.agent_applications import AgentApplication, AgentApplicationStatus


class FakeApplicationRepo:
    async def get_latest_by_telegram_id(self, telegram_id: str):
        if telegram_id != "12345":
            return None
        return AgentApplication(
            id=uuid4(),
            telegram_id="12345",
            full_name="Selam Tadesse",
            phone_number="+251911234567",
            city="Addis Ababa",
            preferred_market_code="merkato",
            visit_frequency="daily",
            status=AgentApplicationStatus.PENDING,
            consent_honest_reporting=True,
            created_at=datetime(2026, 7, 25, tzinfo=UTC),
        )


class FakeRewardRepo:
    async def list_redeem_requests_by_telegram_id(self, telegram_id: str, *, limit: int = 50):
        _ = limit
        if telegram_id != "12345":
            return []
        return [
            type(
                "Row",
                (),
                {
                    "id": uuid4(),
                    "contributor_id": uuid4(),
                    "telegram_id": "12345",
                    "points_redeemed": 500,
                    "birr_per_point": 1,
                    "birr_amount": 500,
                    "currency_code": "ETB",
                    "status": "pending",
                    "admin_note": None,
                    "created_at": datetime(2026, 7, 25, tzinfo=UTC),
                    "resolved_at": None,
                },
            )()
        ]


@pytest.fixture
def client():
    app.dependency_overrides[get_agent_application_repository] = lambda: FakeApplicationRepo()
    app.dependency_overrides[get_reward_settings_repository] = lambda: FakeRewardRepo()
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_agent_application(client: AsyncClient) -> None:
    response = await client.get("/api/v1/agents/applications/12345")
    assert response.status_code == 200
    assert response.json()["telegram_id"] == "12345"


@pytest.mark.asyncio
async def test_get_agent_application_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/agents/applications/missing")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_agent_redeem_requests(client: AsyncClient) -> None:
    response = await client.get("/api/v1/agents/12345/redeem-requests")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["points_redeemed"] == 500
