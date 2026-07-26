from app.services.addis_chat import _extract_model, _extract_text


def test_extract_text_nested_success_payload() -> None:
    text = _extract_text(
        {
            "status": "success",
            "data": {
                "response_text": "Basket is 5660 ETB.",
                "modelVersion": "Addis-1-Alef",
            },
        }
    )
    assert text == "Basket is 5660 ETB."


def test_extract_text_top_level_fallback() -> None:
    assert _extract_text({"response_text": "ok"}) == "ok"


def test_extract_text_empty() -> None:
    assert _extract_text({"status": "success", "data": {}}) == ""


def test_extract_model_nested() -> None:
    assert (
        _extract_model(
            {"status": "success", "data": {"modelVersion": "Addis-፩-አሌፍ"}}
        )
        == "Addis-፩-አሌፍ"
    )
