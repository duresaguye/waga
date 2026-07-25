"""Admin dashboard aggregation."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_applications import AgentApplicationStatus
from app.models.enums import DataTier, EnterpriseEnquiryStatus, SubscriptionStatus
from app.repositories.agent_applications import AgentApplicationRepository
from app.repositories.reward_settings import RewardSettingsRepository
from app.repositories.subscriptions import SubscriptionRepository

PRO_MRR = 29
ENTERPRISE_MRR = 499


class AdminDashboardService:
    def __init__(
        self,
        session: AsyncSession,
        applications: AgentApplicationRepository,
        subscriptions: SubscriptionRepository,
        rewards: RewardSettingsRepository,
    ) -> None:
        self._session = session
        self._applications = applications
        self._subscriptions = subscriptions
        self._rewards = rewards

    async def get_dashboard(self) -> dict:
        applications = await self._applications.list_by_status(limit=1000)
        accounts = await self._subscriptions.list_subscriptions()
        enquiries = await self._subscriptions.list_enquiries()
        redemptions = await self._rewards.list_redeem_requests(limit=1000)

        agent_counts = Counter(app.status.value for app in applications)
        subscription_rows = [subscription for _, subscription in accounts]
        tier_counts = Counter(row.tier.value for row in subscription_rows)
        status_counts = Counter(row.status.value for row in subscription_rows)
        enquiry_counts = Counter(enquiry.status.value for enquiry in enquiries)
        redemption_counts = Counter(row.status for row in redemptions)

        stats = {
            "pending_agents": agent_counts.get(AgentApplicationStatus.PENDING.value, 0),
            "approved_agents": agent_counts.get(AgentApplicationStatus.APPROVED.value, 0),
            "rejected_agents": agent_counts.get(AgentApplicationStatus.REJECTED.value, 0),
            "total_accounts": len(accounts),
            "pro_accounts": tier_counts.get(DataTier.PROFESSIONAL.value, 0),
            "enterprise_accounts": tier_counts.get(DataTier.ENTERPRISE.value, 0),
            "trial_accounts": status_counts.get(SubscriptionStatus.TRIAL.value, 0),
            "active_accounts": status_counts.get(SubscriptionStatus.ACTIVE.value, 0),
            "new_enquiries": enquiry_counts.get(EnterpriseEnquiryStatus.NEW.value, 0),
            "total_enquiries": len(enquiries),
            "pending_redemptions": redemption_counts.get("pending", 0),
            "completed_redemptions": redemption_counts.get("paid", 0),
            "total_redemption_points": sum(row.points_redeemed for row in redemptions),
        }

        mrr_estimate = (
            stats["pro_accounts"] * PRO_MRR + stats["enterprise_accounts"] * ENTERPRISE_MRR
        )
        conversion_rate = 0
        if stats["total_enquiries"]:
            converted = stats["pro_accounts"] + stats["enterprise_accounts"]
            conversion_rate = round((converted / stats["total_enquiries"]) * 100)

        analytics = {
            "weekly_activity": _weekly_activity(
                applications=applications,
                accounts=accounts,
                enquiries=enquiries,
                redemptions=redemptions,
            ),
            "subscription_mix": [
                {"label": "Trial", "value": stats["trial_accounts"]},
                {"label": "Active", "value": stats["active_accounts"]},
                {"label": "Pro", "value": stats["pro_accounts"]},
                {"label": "Enterprise", "value": stats["enterprise_accounts"]},
            ],
            "enquiry_pipeline": [
                {"label": stage.value.title(), "value": enquiry_counts.get(stage.value, 0)}
                for stage in EnterpriseEnquiryStatus
            ],
            "redemption_trend": _redemption_trend(redemptions),
            "operations_load": [
                {"label": "Agents", "value": stats["pending_agents"] + stats["approved_agents"]},
                {"label": "Accounts", "value": stats["total_accounts"]},
                {"label": "Leads", "value": stats["total_enquiries"]},
                {"label": "Payouts", "value": stats["pending_redemptions"] + stats["completed_redemptions"]},
            ],
            "mrr_estimate": mrr_estimate,
            "conversion_rate": conversion_rate,
        }

        badges = {
            "agents": stats["pending_agents"],
            "accounts": stats["total_accounts"],
            "enterprise": stats["new_enquiries"],
            "redemptions": stats["pending_redemptions"],
        }

        return {"stats": stats, "analytics": analytics, "badges": badges}


def _weekly_activity(
    *,
    applications,
    accounts,
    enquiries,
    redemptions,
) -> list[dict]:
    now = datetime.now(UTC)
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    counts = [0] * 7

    def bucket(created_at: datetime) -> int | None:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        if created_at < now - timedelta(days=7):
            return None
        return created_at.weekday()

    for app in applications:
        index = bucket(app.created_at)
        if index is not None:
            counts[index] += 1
    for user, _subscription in accounts:
        index = bucket(user.created_at)
        if index is not None:
            counts[index] += 1
    for enquiry in enquiries:
        index = bucket(enquiry.created_at)
        if index is not None:
            counts[index] += 1
    for redemption in redemptions:
        index = bucket(redemption.created_at)
        if index is not None:
            counts[index] += 1

    return [{"label": label, "value": counts[index]} for index, label in enumerate(labels)]


def _redemption_trend(redemptions) -> list[dict]:
    now = datetime.now(UTC)
    buckets = [0, 0, 0, 0]
    for redemption in redemptions:
        created_at = redemption.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        age_days = (now - created_at).days
        if age_days <= 7:
            buckets[0] += 1
        elif age_days <= 14:
            buckets[1] += 1
        elif age_days <= 21:
            buckets[2] += 1
        else:
            buckets[3] += 1
    return [
        {"label": "W1", "value": buckets[0]},
        {"label": "W2", "value": buckets[1]},
        {"label": "W3", "value": buckets[2]},
        {"label": "W4", "value": buckets[3]},
    ]
