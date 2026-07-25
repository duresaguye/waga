from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.models.enums import SubmissionSource
from app.models.submissions import Submission
from app.services.index_calculation import (
    recency_weight,
    weighted_median,
    _build_weighted_values,
)


def test_recency_weight_at_window_edges() -> None:
    start = datetime(2026, 7, 22, tzinfo=UTC)
    end = datetime(2026, 7, 25, tzinfo=UTC)
    assert recency_weight(start, window_start=start, window_end=end) == pytest.approx(0.5)
    assert recency_weight(end, window_start=start, window_end=end) == pytest.approx(1.0)


def test_weighted_median_single_value() -> None:
    assert weighted_median([(Decimal("100"), 1.0)]) == Decimal("100")


def test_weighted_median_prefers_heavier_side() -> None:
    result = weighted_median(
        [
            (Decimal("80"), 1.0),
            (Decimal("120"), 3.0),
        ]
    )
    assert result == Decimal("120")


def test_build_weighted_values_applies_source_and_recency() -> None:
    start = datetime(2026, 7, 22, tzinfo=UTC)
    end = datetime(2026, 7, 25, tzinfo=UTC)
    submission = Submission(
        client_submission_id=__import__("uuid").uuid4(),
        price_canonical=Decimal("100"),
        unit_canonical="kg",
        received_at=end,
        source=SubmissionSource.AGENT,
        parse_status="parsed",
        parse_method="structured",
    )
    values = _build_weighted_values(
        [{"submission": submission, "contributor": None}],
        window_start=start,
        window_end=end,
    )
    assert len(values) == 1
    assert values[0][0] == Decimal("100")
    assert values[0][1] == pytest.approx(2.0)
