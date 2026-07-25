from app.models.enums import Script
from app.services.text_normalization import (
    detect_script,
    normalize_label,
    resolve_commodity_code_from_memory,
)


def test_normalize_latin_typos() -> None:
    assert normalize_label("  Teff ") == "teff"
    assert normalize_label("Cooking  Oil") == "cooking oil"


def test_detect_ethiopic() -> None:
    assert detect_script("ጤፍ") == Script.ETHIOPIC
    assert detect_script("teff") == Script.ENGLISH


def test_resolve_staple_synonyms() -> None:
    assert resolve_commodity_code_from_memory("tef") == "teff_mixed"
    assert resolve_commodity_code_from_memory("ጤፍ") == "teff_mixed"
    assert resolve_commodity_code_from_memory("xafii") == "teff_mixed"
    assert resolve_commodity_code_from_memory("shinkurt") == "onion"
    assert resolve_commodity_code_from_memory("qamadii") == "wheat"
    assert resolve_commodity_code_from_memory("unknown food") is None
