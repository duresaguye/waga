from enum import StrEnum


class ContributorKind(StrEnum):
    USER = "user"
    AGENT = "agent"
    TEAM = "team"


class AgentScoreEventType(StrEnum):
    PENDING_SUBMIT = "pending_submit"
    ACCEPTED = "accepted"
    FLAGGED = "flagged"
    REDEEM = "redeem"
    ACTIVATE = "activate"
    BAN = "ban"


class InputMode(StrEnum):
    REST = "rest"
    TELEGRAM = "telegram"


class IndexStatus(StrEnum):
    PUBLISHED = "published"
    INSUFFICIENT_DATA = "insufficient_data"


class LicenceClass(StrEnum):
    COMMERCIAL_PERMITTED = "commercial_permitted"
    INTERNAL_ONLY = "internal_only"
    DISPLAY_ONLY = "display_only"


class ParseMethod(StrEnum):
    STRUCTURED = "structured"
    DICTIONARY = "dictionary"
    FUZZY = "fuzzy"


class ParseStatus(StrEnum):
    PARSED = "parsed"
    AMBIGUOUS = "ambiguous"
    UNPARSED = "unparsed"


class ReviewOutcome(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    FLAGGED = "flagged"


class Script(StrEnum):
    ETHIOPIC = "ethiopic"
    LATIN = "latin"
    ENGLISH = "english"


class SubmissionSource(StrEnum):
    USER = "user"
    AGENT = "agent"
    SCRAPED = "scraped"
    SEED = "seed"


class UserRole(StrEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    SUBSCRIBER = "subscriber"


class DataTier(StrEnum):
    PUBLIC = "public"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(StrEnum):
    NONE = "none"
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingPlan(StrEnum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class GateFeature(StrEnum):
    HISTORY = "history"
    SOURCE = "source"
    CONFIDENCE = "confidence"
    COMPARISON = "comparison"
    MAP = "map"
    EXPORT = "export"
    API = "api"
    BASKET = "basket"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentProvider(StrEnum):
    CHAPA = "chapa"


class UpdateFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class EnterpriseEnquiryStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONTRACTED = "contracted"
    CLOSED = "closed"


class SubscriberLanguage(StrEnum):
    EN = "en"
    AM = "am"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


def enum_values[EnumT: StrEnum](enum_class: type[EnumT]) -> list[str]:
    return [item.value for item in enum_class]
