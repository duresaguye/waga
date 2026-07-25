"""Seed a demo administrator account for local development and Hackaton admin app."""

from __future__ import annotations

import asyncio

from app.config import get_settings
from app.database import session_factory
from app.repositories.auth_sessions import AuthSessionRepository
from app.repositories.contributors import ContributorRepository
from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.users import UserRepository
from app.security import JWTService, PasswordService
from app.services.auth import AuthService
from app.services.exceptions import PasswordPolicyError


async def seed() -> None:
    settings = get_settings()
    email = settings.seed_admin_email.strip().lower()
    password = settings.seed_admin_password.get_secret_value()
    display_name = settings.seed_admin_display_name

    async with session_factory() as session:
        service = AuthService(
            session,
            UserRepository(session),
            AuthSessionRepository(session),
            ContributorRepository(session),
            InviteTokenRepository(session),
            PasswordService(),
            JWTService(settings),
            settings,
        )
        try:
            user, created = await service.ensure_admin_user(
                email,
                password,
                display_name,
            )
        except PasswordPolicyError as error:
            raise SystemExit(str(error)) from error

        if created:
            print(f"admin + {email}")
        else:
            print(f"admin = {email}")
        print(f"Admin login: {email} / (see WAGA_SEED_ADMIN_PASSWORD in .env)")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
