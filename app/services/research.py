"""Research-tier snapshots, methodology, and codebook."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.config import Settings
from app.models.enums import IndexStatus
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.services.index_calculation import SOURCE_WEIGHTS
from app.services.prices_read import PricesReadService
from app.services.read_meta import build_meta, snapshot_id


class ResearchService:
    def __init__(
        self,
        prices: PricesReadService,
        reference_data: ReferenceDataRepository,
        index_values: IndexValueRepository,
        settings: Settings,
    ) -> None:
        self._prices = prices
        self._reference_data = reference_data
        self._index_values = index_values
        self._settings = settings

    async def get_snapshots(self) -> dict:
        markets = await self._reference_data.list_markets(active_only=True)
        commodities = await self._reference_data.list_commodities(active_only=True)
        latest = await self._prices._load_latest_cells(markets, commodities)
        now = datetime.now(UTC)
        snap = snapshot_id(now, self._settings.method_version)
        published = sum(1 for row in latest if row.status == IndexStatus.PUBLISHED)
        insufficient = len(latest) - published
        end = date.today()
        start = end - timedelta(days=90)
        rows = await self._index_values.list_panel_rows(
            start=datetime.combine(start, datetime.min.time(), tzinfo=UTC),
            end=datetime.combine(end, datetime.max.time(), tzinfo=UTC),
        )
        meta = build_meta(
            self._settings,
            latest_values=latest,
            matrix_size=len(markets) * len(commodities),
        )
        return {
            "meta": meta,
            "data": {
                "snapshots": [
                    {
                        "snapshot_id": snap,
                        "created_at": meta["generated_at"],
                        "method_version": self._settings.method_version,
                        "temporal_coverage": {
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                        },
                        "spatial_coverage": {
                            "city": self._settings.city_code,
                            "markets": len(markets),
                        },
                        "commodities": len(commodities),
                        "row_count": len(rows),
                        "rows_published": published,
                        "rows_insufficient": insufficient,
                        "licence": "CC-BY-4.0",
                        "checksum_sha256": "pending",
                        "citation": (
                            f"Waga Intelligence ({end.year}). Addis Ababa Market Price Index, "
                            f"snapshot {snap}. https://waga.et/data/{snap}"
                        ),
                        "download": {
                            "csv": f"/api/v1/exports/panel.csv?snapshot={snap}",
                            "parquet": None,
                        },
                        "immutable": True,
                    }
                ]
            },
        }

    async def get_methodology(self) -> dict:
        latest = await self._prices._load_latest_cells(
            await self._reference_data.list_markets(active_only=True),
            await self._reference_data.list_commodities(active_only=True),
        )
        meta = build_meta(self._settings, latest_values=latest)
        return {
            "meta": meta,
            "data": {
                "method_version": self._settings.method_version,
                "effective_from": "2026-04-01",
                "window_hours": self._settings.index_window_hours,
                "publish_threshold_submissions": self._settings.publication_threshold,
                "aggregation": "weighted median",
                "source_weights": {key.value: value for key, value in SOURCE_WEIGHTS.items()},
                "recency_weight": "linear 0.5 → 1.0 across the window",
                "imputation": "none",
                "below_threshold_behaviour": "insufficient_data, value null",
                "changelog": [
                    {
                        "version": self._settings.method_version,
                        "date": "2026-04-01",
                        "change": "Initial release.",
                    }
                ],
            },
        }

    async def get_codebook(self) -> dict:
        meta = build_meta(self._settings, latest_values=[])
        return {
            "meta": meta,
            "data": {
                "columns": [
                    {"name": "date", "type": "date", "description": "Observation date"},
                    {"name": "market", "type": "string", "description": "Market name"},
                    {"name": "commodity", "type": "string", "description": "Commodity name"},
                    {"name": "price", "type": "number", "description": "Published price in ETB"},
                    {"name": "status", "type": "string", "description": "published or insufficient_data"},
                    {"name": "n_submissions", "type": "integer", "description": "Accepted submissions in window"},
                    {"name": "method_version", "type": "string", "description": "Index method version"},
                    {"name": "snapshot_id", "type": "string", "description": "Immutable snapshot identifier"},
                ]
            },
        }
