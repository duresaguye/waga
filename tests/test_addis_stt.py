from telegram_bot.services.addis_stt import _extract_text


def test_extract_transcription() -> None:
    assert (
        _extract_text(
            {
                "status": "success",
                "data": {"transcription": "  Merkato  "},
                "confidence": 0.9,
            }
        )
        == "Merkato"
    )


def test_extract_missing() -> None:
    assert _extract_text({"status": "success", "data": {}}) == ""
