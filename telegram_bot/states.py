from enum import IntEnum, auto


class SubmitState(IntEnum):
    CONSENT = auto()
    ENTRY_MODE = auto()
    MARKET = auto()
    MARKET_OTHER = auto()
    MARKET_OTHER_CONFIRM = auto()
    COMMODITY = auto()
    PRICE = auto()
    CONFIRM = auto()


class ApplyState(IntEnum):
    FULL_NAME = auto()
    PHONE = auto()
    CITY = auto()
    CITY_OTHER = auto()
    SUBCITY = auto()
    SUBCITY_OTHER = auto()
    MARKET = auto()
    MARKET_OTHER = auto()
    MARKET_OTHER_CONFIRM = auto()
    FREQUENCY = auto()
    LANGUAGES = auto()
    CONSENT = auto()
    CONFIRM = auto()
