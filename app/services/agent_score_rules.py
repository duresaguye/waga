"""Shared agent score rules (backend + telegram bot dry-run)."""

POINTS_PENDING = 1
POINTS_ACCEPT = 10
POINTS_FLAG = -15
BAN_SCORE_FLOOR = 0
BAN_FLAG_LIMIT = 3
REDEEM_THRESHOLD = 50


def status_label(*, banned: bool, score: int) -> str:
    if banned:
        return "Banned"
    if score >= 50:
        return "Trusted"
    if score >= 20:
        return "Rising"
    return "Active"
