import hashlib
import hmac
import json
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse
from uuid import UUID, uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.auth import User
from app.models.enums import BillingPlan, PaymentProvider, PaymentStatus
from app.models.subscriptions import PaymentTransaction
from app.repositories.subscriptions import SubscriptionRepository
from app.services.exceptions import (
    ChapaApiError,
    ChapaNotConfiguredError,
    ChapaWebhookInvalidError,
    PaymentNotFoundError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
)
from app.services.subscription_plans import SubscriptionPlanService
from app.services.subscriptions import SubscriptionService, utc_now


class ChapaPaymentService:
    def __init__(
        self,
        session: AsyncSession,
        subscriptions: SubscriptionRepository,
        subscription_service: SubscriptionService,
        plan_service: SubscriptionPlanService,
        settings: Settings,
        clock: Callable[[], datetime] = utc_now,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._session = session
        self._subscriptions = subscriptions
        self._subscription_service = subscription_service
        self._plan_service = plan_service
        self._settings = settings
        self._clock = clock
        self._http = http_client

    async def create_checkout(
        self,
        user: User,
        *,
        plan_id: UUID | None = None,
        billing_plan: BillingPlan | None = None,
    ) -> PaymentTransaction:
        secret_key = self._require_secret_key()
        subscription = await self._subscriptions.get_subscription_by_user_id(user.id)
        if subscription is None:
            await self._session.rollback()
            raise SubscriptionNotFoundError

        try:
            plan = await self._plan_service.get_checkout_plan(
                plan_id=plan_id,
                billing_plan=billing_plan,
            )
        except PlanNotFoundError as error:
            await self._session.rollback()
            raise error

        resolved_billing_plan = plan.billing_plan
        if resolved_billing_plan is None:
            await self._session.rollback()
            raise PlanNotFoundError("Selected plan has no billing cadence")

        payment_id = uuid4()
        tx_ref = f"waga-{payment_id}"
        amount = plan.amount_etb
        payment = PaymentTransaction(
            id=payment_id,
            user_id=user.id,
            provider=PaymentProvider.CHAPA,
            amount_etb=amount,
            billing_plan=resolved_billing_plan,
            plan_id=plan.id,
            status=PaymentStatus.PENDING,
            tx_ref=tx_ref,
        )
        self._subscriptions.add_payment(payment)
        await self._session.flush()

        first_name, last_name = self._split_name(user.display_name)
        return_url = self._return_url_for_payment(payment_id)
        payload = {
            "amount": str(int(amount)),
            "currency": "ETB",
            "email": user.email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": self._settings.chapa_callback_url,
            "return_url": return_url,
            "customization": {
                "title": "Waga Intelligence",
                "description": f"{plan.name_en} ({resolved_billing_plan.value})",
            },
        }

        response = await self._request(
            "POST",
            "/transaction/initialize",
            secret_key=secret_key,
            json_body=payload,
        )
        checkout_url = response.get("data", {}).get("checkout_url")
        if not isinstance(checkout_url, str) or not checkout_url.strip():
            await self._session.rollback()
            raise ChapaApiError("Chapa initialize did not return a checkout URL")

        payment.checkout_url = checkout_url
        await self._session.commit()
        return payment

    async def verify_and_finalize(self, tx_ref: str) -> PaymentTransaction:
        secret_key = self._require_secret_key()
        payment = await self._subscriptions.get_payment_by_tx_ref(tx_ref, for_update=True)
        if payment is None:
            await self._session.rollback()
            raise PaymentNotFoundError
        if payment.status != PaymentStatus.PENDING:
            await self._session.rollback()
            return payment

        response = await self._request(
            "GET",
            f"/transaction/verify/{tx_ref}",
            secret_key=secret_key,
        )
        now = self._clock()
        data = response.get("data")
        if not isinstance(data, dict):
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "chapa_verify_invalid_response"
            payment.confirmed_at = now
            await self._session.commit()
            return payment

        chapa_status = str(data.get("status", "")).lower()
        if response.get("status") == "success" and chapa_status == "success":
            payment.status = PaymentStatus.SUCCEEDED
            payment.chapa_ref_id = self._extract_ref_id(data)
            payment.confirmed_at = now
            await self._session.commit()
            tier = None
            if payment.plan_id is not None:
                plan = await self._plan_service.get_plan(payment.plan_id)
                tier = plan.tier
            await self._subscription_service.activate_subscription(
                payment.user_id,
                payment.billing_plan,
                plan_id=payment.plan_id,
                tier=tier,
            )
            return payment

        payment.status = PaymentStatus.FAILED
        payment.failure_reason = chapa_status or "chapa_payment_failed"
        payment.confirmed_at = now
        await self._session.commit()
        return payment

    async def get_checkout_status(
        self,
        user: User,
        payment_id: UUID,
    ) -> PaymentTransaction:
        payment = await self._subscriptions.get_payment_by_id(payment_id, for_update=True)
        if payment is None or payment.user_id != user.id:
            await self._session.rollback()
            raise PaymentNotFoundError
        if payment.status == PaymentStatus.PENDING:
            await self._session.rollback()
            return await self.verify_and_finalize(payment.tx_ref)
        await self._session.rollback()
        return payment

    def verify_webhook_signature(self, body: bytes, signature: str | None) -> None:
        secret = self._settings.chapa_webhook_secret_value()
        if not secret:
            raise ChapaNotConfiguredError
        if not signature:
            raise ChapaWebhookInvalidError
        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature.strip()):
            raise ChapaWebhookInvalidError

    async def handle_webhook_payload(self, payload: dict[str, Any]) -> PaymentTransaction:
        tx_ref = payload.get("tx_ref") or payload.get("trx_ref")
        if not isinstance(tx_ref, str) or not tx_ref.strip():
            raise PaymentNotFoundError
        return await self.verify_and_finalize(tx_ref.strip())

    def _require_secret_key(self) -> str:
        secret_key = self._settings.chapa_secret_key()
        if not secret_key:
            raise ChapaNotConfiguredError
        return secret_key

    async def _request(
        self,
        method: str,
        path: str,
        *,
        secret_key: str,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._settings.chapa_base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {secret_key}"}
        client = self._http or httpx.AsyncClient(timeout=30.0)
        owns_client = self._http is None
        try:
            if method == "POST":
                response = await client.post(url, json=json_body, headers=headers)
            else:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError as error:
            raise ChapaApiError("Chapa API request failed") from error
        finally:
            if owns_client:
                await client.aclose()

        try:
            body = response.json()
        except json.JSONDecodeError as error:
            raise ChapaApiError("Chapa API returned invalid JSON") from error

        if response.status_code >= 400 or body.get("status") != "success":
            message = body.get("message")
            detail = message if isinstance(message, str) else "Chapa API error"
            raise ChapaApiError(detail)

        if not isinstance(body, dict):
            raise ChapaApiError("Chapa API returned an unexpected payload")
        return body

    @staticmethod
    def _split_name(display_name: str | None) -> tuple[str, str]:
        if not display_name or not display_name.strip():
            return "Waga", "Subscriber"
        parts = display_name.strip().split(maxsplit=1)
        if len(parts) == 1:
            return parts[0], "Subscriber"
        return parts[0], parts[1]

    def _return_url_for_payment(self, payment_id: UUID) -> str:
        base = self._settings.chapa_return_url.strip()
        parsed = urlparse(base)
        query = dict[str, str]()
        if parsed.query:
            for pair in parsed.query.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    query[key] = value
        query["payment_id"] = str(payment_id)
        return urlunparse(parsed._replace(query=urlencode(query)))

    @staticmethod
    def _extract_ref_id(data: dict[str, Any]) -> str | None:
        for key in ("reference", "ref_id", "id"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
