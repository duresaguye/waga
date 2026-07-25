import argparse
import asyncio
import sys
from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.config import get_settings
from app.database import engine, session_factory
from app.models.auth import User
from app.models.enums import UserRole
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.contributors import ContributorRepository
from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.users import UserRepository
from app.security import JWTService, PasswordService
from app.services.auth import AuthService
from app.services.exceptions import (
    EmailAlreadyRegisteredError,
    InitialAdminAlreadyExistsError,
    PasswordPolicyError,
)

email_adapter: TypeAdapter[EmailStr] = TypeAdapter(EmailStr)


def _auth_service(session):  # type: ignore[no-untyped-def]
    settings = get_settings()
    return AuthService(
        session,
        UserRepository(session),
        AuthSessionRepository(session),
        ContributorRepository(session),
        InviteTokenRepository(session),
        PasswordService(),
        JWTService(settings),
        settings,
    )


async def create_admin(email: str, display_name: str | None, password: str) -> None:
    async with session_factory() as session:
        service = _auth_service(session)
        user = await service.create_initial_admin(email, password, display_name)
        print(f"Created initial admin {user.email} ({user.id})")


async def reset_admin_password(email: str, password: str) -> None:
    async with session_factory() as session:
        service = _auth_service(session)
        service._validate_password(password)  # noqa: SLF001
        users = UserRepository(session)
        passwords = PasswordService()

        user = await users.get_by_email(email)
        if user is None:
            raise LookupError(f"No user found for {email}")
        if user.role != UserRole.ADMIN:
            raise LookupError(f"{email} exists but is not an admin")

        user.password_hash = await passwords.hash(password)
        user.auth_version = int(user.auth_version or 1) + 1
        user.failed_login_attempts = 0
        user.locked_until = None
        await session.commit()
        print(f"Password reset for admin {user.email}")


async def list_admins() -> None:
    async with session_factory() as session:
        rows = (
            await session.execute(
                select(User.email, User.status).where(User.role == UserRole.ADMIN)
            )
        ).all()
        if not rows:
            print("No admin users found.")
            return
        print("Existing admins:")
        for email, status in rows:
            print(f"  - {email} ({status})")


async def _run(coro):  # type: ignore[no-untyped-def]
    try:
        await coro
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset the Waga administrator")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--display-name", help="Administrator display name")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset password for an existing admin email",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing admin emails",
    )
    args = parser.parse_args()

    if args.list:
        try:
            asyncio.run(_run(list_admins()))
        except Exception as error:  # noqa: BLE001
            print(f"Failed: {error}", file=sys.stderr)
            raise SystemExit(1) from None
        return

    raw_email = args.email or input("Email: ").strip()
    try:
        email = str(email_adapter.validate_python(raw_email))
    except ValidationError as error:
        parser.error(f"invalid email address: {error.errors()[0]['msg']}")

    password = getpass("Password: ")
    password_confirmation = getpass("Confirm password: ")
    if password != password_confirmation:
        parser.error("passwords do not match")

    try:
        if args.reset_password:
            asyncio.run(_run(reset_admin_password(email, password)))
        else:
            asyncio.run(_run(create_admin(email, args.display_name, password)))
    except InitialAdminAlreadyExistsError:
        print(
            "An administrator already exists.\n"
            "List:   uv run waga-create-admin --list\n"
            "Reset:  uv run waga-create-admin --email EXISTING@email --reset-password"
        )
        raise SystemExit(2) from None
    except EmailAlreadyRegisteredError:
        print("That email is already registered.")
        raise SystemExit(2) from None
    except PasswordPolicyError as error:
        print(str(error))
        raise SystemExit(2) from None
    except LookupError as error:
        print(str(error))
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
