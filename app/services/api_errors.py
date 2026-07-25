"""Contract-shaped API errors for read endpoints."""

from __future__ import annotations


class ContractError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        field: str | None = None,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.field = field
        self.status_code = status_code
        super().__init__(message)


def contract_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    status_code: int = 400,
) -> ContractError:
    return ContractError(code, message, field=field, status_code=status_code)


def error_body(code: str, message: str, *, field: str | None = None) -> dict:
    payload: dict = {"code": code, "message": message}
    if field is not None:
        payload["field"] = field
    return {"error": payload}
