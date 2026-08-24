from translator.engine import translate


def test_translate_returns_nonempty_string():
    result = translate("hello", "en", "es")
    assert isinstance(result, str)
    assert len(result) > 0


def test_translate_invalid_language_raises():
    import pytest
    with pytest.raises(Exception):
        translate("hello", "en", "not-a-real-language-code")
