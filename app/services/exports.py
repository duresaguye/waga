"""CSV export for published index panel."""

from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import IndexStatus
from app.repositories.index_values import IndexValueRepository
from app.repositories.reference_data import ReferenceDataRepository
from app.services.read_meta import snapshot_id


class ExportService:
    def __init__(
        self,
        session: AsyncSession,
        reference_data: ReferenceDataRepository,
        index_values: IndexValueRepository,
        settings: Settings,
    ) -> None:
        self._session = session
        self._reference_data = reference_data
        self._index_values = index_values
        self._settings = settings

    async def panel_csv(
        self,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> str:
        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=30))
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=UTC)
        rows = await self._index_values.list_panel_rows(start=start_dt, end=end_dt)
        generated_at = datetime.now(UTC)
        snap = snapshot_id(generated_at, self._settings.method_version)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "date",
                "admin1",
                "admin2",
                "market",
                "latitude",
                "longitude",
                "category",
                "commodity",
                "unit",
                "priceflag",
                "pricetype",
                "currency",
                "price",
                "usdprice",
                "n_submissions",
                "n_contributors",
                "source_mix",
                "status",
                "method_version",
                "snapshot_id",
            ]
        )
        writer.writerow(
            [
                "#date",
                "#adm1+name",
                "#adm2+name",
                "#loc+market+name",
                "#geo+lat",
                "#geo+lon",
                "#item+type",
                "#item+name",
                "#item+unit",
                "#item+price+flag",
                "#item+price+type",
                "#currency",
                "#value",
                "#value+usd",
                "#meta+count",
                "#meta+contributors",
                "#meta+sources",
                "#status+code",
                "#meta+method",
                "#meta+snapshot",
            ]
        )

        for row in rows:
            index_value = row["index_value"]
            market = row["market"]
            commodity = row["commodity"]
            source_mix = "|".join(
                f"{key}:{value}" for key, value in sorted(index_value.source_mix.items())
            )
            writer.writerow(
                [
                    index_value.computed_at.date().isoformat(),
                    "Addis Ababa",
                    "Addis Ababa",
                    market.name_en,
                    float(market.latitude) if market.latitude is not None else "",
                    float(market.longitude) if market.longitude is not None else "",
                    "staples",
                    commodity.name_en,
                    index_value.unit.upper(),
                    "actual",
                    "Retail",
                    self._settings.currency_code,
                    float(index_value.value)
                    if index_value.status == IndexStatus.PUBLISHED
                    and index_value.value is not None
                    else "",
                    "",
                    index_value.n_submissions,
                    index_value.n_contributors,
                    source_mix,
                    index_value.status.value,
                    index_value.method_version,
                    snap,
                ]
            )
        return buffer.getvalue()
