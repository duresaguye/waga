from app.services.agent_score import AgentScoreService


def test_generated_invite_code_shape() -> None:
    code = AgentScoreService.generate_invite_code()
    assert code.startswith("WAGA-")
    parts = code.split("-")
    assert len(parts) == 4
    assert all(len(part) == 4 for part in parts[1:])
    # Should not look like the old guessable pilot code.
    assert code.lower() != "waga-addis-01"


def test_generated_codes_are_unique_enough() -> None:
    codes = {AgentScoreService.generate_invite_code() for _ in range(50)}
    assert len(codes) == 50
