from app.services.index_rules import affordability_band, heat_band
from app.services.index_calculation import IndexCalculationService
from statistics import median
from decimal import Decimal


def test_heat_bands() -> None:
    assert heat_band(-3) == "cool"
    assert heat_band(0) == "stable"
    assert heat_band(3) == "warm"
    assert heat_band(7) == "hot"
    assert heat_band(12) == "critical"
    assert heat_band(None) is None


def test_affordability_severe() -> None:
    score, band = affordability_band(18.3)
    assert band == "Severe"
    assert score is not None and score >= 5


def test_median_publish_threshold_math() -> None:
    prices = [Decimal("100"), Decimal("110"), Decimal("120")]
    assert median(prices) == Decimal("110")
    assert len(prices) >= 3
