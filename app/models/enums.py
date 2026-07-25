from enum import StrEnum


class ContributorKind(StrEnum):
    USER = "user"
    AGENT = "agent"
    TEAM = "team"


class InputMode(StrEnum):
    REST = "rest"


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


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


def enum_values[EnumT: StrEnum](enum_class: type[EnumT]) -> list[str]:
    return [item.value for item in enum_class]
