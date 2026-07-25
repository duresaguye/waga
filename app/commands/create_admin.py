import argparse
import asyncio
from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.config import get_settings
from app.database import engine, session_factory
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.contributors import ContributorRepository
from app.repositories.users import UserRepository
from app.security import JWTService, PasswordService
from app.services.auth import AuthService
from app.services.exceptions import (
    EmailAlreadyRegisteredError,
    InitialAdminAlreadyExistsError,
    PasswordPolicyError,
)

email_adapter: TypeAdapter[EmailStr] = TypeAdapter(EmailStr)


async def create_admin(email: str, display_name: str | None, password: str) -> None:
    settings = get_settings()
    async with session_factory() as session:
        service = AuthService(
            session,
            UserRepository(session),
            AuthSessionRepository(session),
            ContributorRepository(session),
            PasswordService(),
            JWTService(settings),
            settings,
        )
        user = await service.create_initial_admin(email, password, display_name)
        print(f"Created initial admin {user.email} ({user.id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first Waga administrator")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--display-name", help="Administrator display name")
    args = parser.parse_args()

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
        asyncio.run(create_admin(email, args.display_name, password))
    except InitialAdminAlreadyExistsError:
        parser.error("an administrator already exists")
    except EmailAlreadyRegisteredError:
        parser.error("the email address is already registered")
    except PasswordPolicyError as error:
        parser.error(str(error))
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
