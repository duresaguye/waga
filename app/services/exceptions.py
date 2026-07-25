class AuthError(Exception):
    """Base exception for authentication failures."""


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidAccessTokenError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class PasswordPolicyError(AuthError):
    pass


class CurrentPasswordInvalidError(AuthError):
    pass


class PasswordReuseError(AuthError):
    pass


class InitialAdminAlreadyExistsError(AuthError):
    pass


class InviteTokenNotFoundError(AuthError):
    pass


class InviteTokenExpiredError(AuthError):
    pass


class InviteTokenAlreadyUsedError(AuthError):
    pass


class ReferenceDataError(Exception):
    """Base exception for reference data operations."""


class ReferenceDataNotFoundError(ReferenceDataError):
    pass


class ReferenceDataConflictError(ReferenceDataError):
    pass
