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


class AgentScoreError(Exception):
    """Base exception for agent score operations."""


class AgentNotFoundError(AgentScoreError):
    pass


class AgentInviteInvalidError(AgentScoreError):
    pass


class AgentBannedError(AgentScoreError):
    pass


class AgentRedeemNotReadyError(AgentScoreError):
    pass


class AgentApplicationNotFoundError(AgentScoreError):
    pass


class AgentApplicationConflictError(AgentScoreError):
    pass


class SubmissionError(Exception):
    """Base exception for submission operations."""


class SubmissionValidationError(SubmissionError):
    pass


class SubmissionConflictError(SubmissionError):
    pass
