from app.services.agent_score_rules import (
    POINTS_ACCEPT,
    POINTS_FLAG,
    POINTS_PENDING,
    REDEEM_THRESHOLD,
    status_label,
)


def test_score_point_constants() -> None:
    assert POINTS_PENDING == 1
    assert POINTS_ACCEPT == 10
    assert POINTS_FLAG == -15
    assert REDEEM_THRESHOLD == 50


def test_status_label_transitions() -> None:
    assert status_label(banned=True, score=100) == "Banned"
    assert status_label(banned=False, score=50) == "Trusted"
    assert status_label(banned=False, score=20) == "Rising"
    assert status_label(banned=False, score=0) == "Active"


def test_accept_path_net_points_from_pending() -> None:
    # pending +1, then accept adjusts by +9 → net +10 from start
    score = 0
    score += POINTS_PENDING
    score += POINTS_ACCEPT - POINTS_PENDING
    assert score == POINTS_ACCEPT
