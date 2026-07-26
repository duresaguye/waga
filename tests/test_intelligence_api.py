import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import (
    get_affordability_service,
    get_alerts_service,
    get_brief_service,
    get_copilot_service,
    get_prices_read_service,
    get_research_service,
)
from app.main import app
from app.services.api_errors import contract_error


class FakeAffordabilityService:
    async def get_affordability(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {
                "basket_code": "phase1_staple5",
                "status": "insufficient_data",
                "cost_now": None,
                "missing_commodities": ["teff_mixed"],
            },
        }

    async def get_meb_food_line(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {"waga_food_line_now": None, "change_pct": None},
        }


class FakeCopilotService:
    async def ask(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {
                "answer": "test",
                "citations": [],
                "mode": "rule_based",
                "recommendation": {
                    "action": "increase_transfer_value",
                    "band_low_pct": 10.0,
                    "band_high_pct": 16.0,
                    "confidence": "medium",
                    "confidence_reason": "test",
                },
                "impact": {
                    "household_count": 50000,
                    "gap_per_household_etb": 770.0,
                    "monthly_total_etb": 38500000.0,
                },
            },
        }

    async def impact(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {"monthly_total_etb": 37500000.0},
        }


class FakeBriefService:
    async def monthly(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {
                "title": "test brief",
                "markdown": "# test\n",
                "executive_summary": "summary",
                "mode": "template",
            },
        }


class FakeAlertsService:
    async def get_alerts(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-spike-v1"},
            "data": {"alerts": [], "alps_comparable": False},
        }


class FakeResearchService:
    async def get_snapshots(self) -> dict:
        return {"meta": {}, "data": {"snapshots": []}}

    async def get_methodology(self) -> dict:
        return {"meta": {}, "data": {"method_version": "waga-index-v1"}}

    async def get_codebook(self) -> dict:
        return {"meta": {}, "data": {"columns": []}}


class FakePricesReadService:
    async def get_current_prices(self, **kwargs) -> dict:
        if kwargs.get("market_codes") == ["bole"]:
            raise contract_error("unknown_market", "No market with code 'bole'", field="market")
        return {"meta": {}, "data": {"cells": [], "city_prices": []}}


@pytest.fixture
def client():
    app.dependency_overrides[get_affordability_service] = lambda: FakeAffordabilityService()
    app.dependency_overrides[get_copilot_service] = lambda: FakeCopilotService()
    app.dependency_overrides[get_brief_service] = lambda: FakeBriefService()
    app.dependency_overrides[get_alerts_service] = lambda: FakeAlertsService()
    app.dependency_overrides[get_research_service] = lambda: FakeResearchService()
    app.dependency_overrides[get_prices_read_service] = lambda: FakePricesReadService()
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_affordability_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/affordability")
    assert response.status_code == 200
    assert response.json()["data"]["basket_code"] == "phase1_staple5"


@pytest.mark.asyncio
async def test_copilot_and_impact_endpoints(client: AsyncClient) -> None:
    copilot = await client.post(
        "/api/v1/copilot/ask",
        json={"question": "How should we adjust?", "household_count": 50000},
    )
    assert copilot.status_code == 200
    impact = await client.post(
        "/api/v1/impact",
        json={"household_count": 50000, "gap_per_household_etb": 750.0, "months": 3},
    )
    assert impact.status_code == 200


@pytest.mark.asyncio
async def test_monthly_brief_endpoint(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/briefs/monthly",
        json={"household_count": 50000, "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["title"] == "test brief"
    assert "# test" in body["data"]["markdown"]


@pytest.mark.asyncio
async def test_research_endpoints(client: AsyncClient) -> None:
    for path in (
        "/api/v1/research/snapshots",
        "/api/v1/research/methodology",
        "/api/v1/research/codebook",
    ):
        response = await client.get(path)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_unknown_market_returns_contract_error(client: AsyncClient) -> None:
    response = await client.get("/api/v1/prices/current", params={"market": "bole"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "unknown_market"
