"""Phase 1 seed markets and commodities for the Telegram bot.

Well-known Addis Ababa markets + optional free-text "other".
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketOption:
    code: str
    name_en: str
    name_am: str


@dataclass(frozen=True, slots=True)
class CommodityOption:
    code: str
    name_en: str
    name_am: str
    unit: str


# Well-known Addis markets for the pilot (not whole Ethiopia).
MARKETS: tuple[MarketOption, ...] = (
    MarketOption("merkato", "Merkato", "መርካቶ"),
    MarketOption("shola", "Shola Gebeya", "ሾላ ገበያ"),
    MarketOption("ehil_berenda", "Ehil Berenda", "እህል በረንዳ"),
    MarketOption("atikilt_tera", "Atikilt Tera", "አትክልት ተራ"),
    MarketOption("piazza", "Piazza", "ፒያሳ"),
    MarketOption("saris", "Saris", "ሳሪስ"),
    MarketOption("akaki", "Akaki", "አቃቂ"),
    MarketOption("asko", "Asko", "አስኮ"),
    MarketOption("kera", "Kera", "ቄራ"),
    MarketOption("other", "Other (type name)", "ሌላ (ስም ጻፍ)"),
)

COMMODITIES: tuple[CommodityOption, ...] = (
    CommodityOption("teff_mixed", "Teff (mixed)", "ጤፍ (ድብልቅ)", "kg"),
    CommodityOption("wheat", "Wheat", "ስንዴ", "kg"),
    CommodityOption("maize", "Maize", "በቆሎ", "kg"),
    CommodityOption("onion", "Onion", "ሽንኩርት", "kg"),
    CommodityOption("cooking_oil", "Cooking oil", "የምግብ ዘይት", "liter"),
)

CONSENT_VERSION = "contributor-v1"
OTHER_MARKET_CODE = "other"


def market_by_code(code: str) -> MarketOption | None:
    return next((item for item in MARKETS if item.code == code), None)


def commodity_by_code(code: str) -> CommodityOption | None:
    return next((item for item in COMMODITIES if item.code == code), None)
