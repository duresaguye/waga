from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_prices_read_service
from app.main import app


class FakePricesReadService:
    async def get_reference(self) -> dict:
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {
                "city": {"code": "addis_ababa", "name_en": "Addis Ababa", "name_am": "Addis Ababa"},
                "markets": [{"code": "merkato", "name_en": "Merkato", "name_am": "መርካቶ"}],
                "commodities": [{"code": "teff_mixed", "name_en": "Teff (mixed)", "unit": "kg"}],
                "baskets": [{"code": "phase1_staple5"}],
            },
        }

    async def get_current_prices(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {
                "cells": [
                    {
                        "market_code": "merkato",
                        "commodity_code": "teff_mixed",
                        "status": "published",
                        "value": 108.36,
                    }
                ],
                "city_prices": [
                    {
                        "commodity_code": "teff_mixed",
                        "status": "published",
                        "value": 108.36,
                    }
                ],
            },
        }

    async def get_series(self, **kwargs) -> dict:
        _ = kwargs
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {
                "interval": "day",
                "series": [
                    {
                        "commodity_code": "teff_mixed",
                        "market_code": "merkato",
                        "points": [{"date": "2026-07-25", "value": 108.36, "status": "published"}],
                    }
                ],
            },
        }

    async def get_coverage(self) -> dict:
        return {
            "meta": {"method_version": "waga-index-v1"},
            "data": {
                "matrix": [{"market_code": "merkato", "cells": []}],
                "worst_covered": [],
            },
        }


@pytest.fixture
def client():
    app.dependency_overrides[get_prices_read_service] = lambda: FakePricesReadService()
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reference_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["city"]["code"] == "addis_ababa"
    assert body["data"]["baskets"][0]["code"] == "phase1_staple5"


@pytest.mark.asyncio
async def test_prices_current_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/prices/current")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["cells"][0]["status"] == "published"
    assert body["data"]["city_prices"][0]["commodity_code"] == "teff_mixed"


@pytest.mark.asyncio
async def test_prices_series_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/prices/series", params={"commodity": "teff_mixed"})
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["series"][0]["commodity_code"] == "teff_mixed"


@pytest.mark.asyncio
async def test_coverage_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/coverage")
    assert response.status_code == 200
    assert "matrix" in response.json()["data"]
