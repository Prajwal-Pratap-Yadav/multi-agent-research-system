import pytest

from app.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MAX_SOURCES_PER_QUESTION", raising=False)
    s = Settings.from_env()
    assert s.anthropic_api_key is None
    assert s.max_sources_per_question == 3


def test_invalid_int_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_SOURCES_PER_QUESTION", "lots")
    with pytest.raises(ValueError, match="MAX_SOURCES_PER_QUESTION"):
        Settings.from_env()
