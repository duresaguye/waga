from decimal import Decimal

from app.services.review_triage import ReviewTriageService, _parse_llm_json


def test_rules_flag_outside_sanity_band() -> None:
    triage = ReviewTriageService()
    facts = triage.build_facts(
        market_code="merkato",
        commodity_code="teff_mixed",
        price=Decimal("9000"),
        unit="kg",
        agent_score=10,
        agent_accepted_count=2,
        agent_flagged_count=0,
        same_market_accepted_prices=[Decimal("95"), Decimal("100")],
        same_agent_recent_prices=[Decimal("98")],
    )
    result = triage.rules_triage(facts)
    assert result.verdict == "flag"
    assert result.model == "rules-v1"


def test_rules_accept_near_market_median() -> None:
    triage = ReviewTriageService()
    facts = triage.build_facts(
        market_code="merkato",
        commodity_code="teff_mixed",
        price=Decimal("100"),
        unit="kg",
        agent_score=20,
        agent_accepted_count=5,
        agent_flagged_count=0,
        same_market_accepted_prices=[Decimal("95"), Decimal("100"), Decimal("105")],
        same_agent_recent_prices=[Decimal("98"), Decimal("102")],
    )
    result = triage.rules_triage(facts)
    assert result.verdict == "accept"


def test_rules_hold_without_history() -> None:
    triage = ReviewTriageService()
    facts = triage.build_facts(
        market_code="merkato",
        commodity_code="teff_mixed",
        price=Decimal("100"),
        unit="kg",
        agent_score=1,
        agent_accepted_count=0,
        agent_flagged_count=0,
        same_market_accepted_prices=[],
        same_agent_recent_prices=[],
    )
    result = triage.rules_triage(facts)
    assert result.verdict == "hold"


def test_parse_llm_json_plain() -> None:
    parsed = _parse_llm_json(
        '{"verdict":"accept","confidence":"high","reason":"Matches market."}'
    )
    assert parsed == ("accept", "high", "Matches market.")


def test_parse_llm_json_fenced() -> None:
    parsed = _parse_llm_json(
        '```json\n{"verdict":"flag","confidence":"medium","reason":"Too high"}\n```'
    )
    assert parsed is not None
    assert parsed[0] == "flag"
