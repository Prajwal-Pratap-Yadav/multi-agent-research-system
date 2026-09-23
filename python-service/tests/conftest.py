"""Shared test doubles."""

from __future__ import annotations

import pytest

from app.errors import LLMError, SearchError
from app.search import Document

AI_DOC = Document(
    title="Artificial intelligence",
    url="https://en.wikipedia.org/wiki/Artificial_intelligence",
    content=(
        "Artificial intelligence is the capability of computer systems to perform tasks "
        "associated with human intelligence. Applications of artificial intelligence include "
        "search engines, recommendation systems and autonomous vehicles. Critics of artificial "
        "intelligence raise concerns about bias, privacy and job displacement."
    ),
)
ML_DOC = Document(
    title="Machine learning",
    url="https://en.wikipedia.org/wiki/Machine_learning",
    content=(
        "Machine learning is a field of artificial intelligence concerned with statistical "
        "algorithms that learn from data. Deep learning advances drove recent intelligence "
        "breakthroughs in the history of the field."
    ),
)


class FakeSearch:
    """Search provider returning canned documents; can be told to fail."""

    def __init__(self, docs: list[Document] | None = None, fail: bool = False) -> None:
        self.docs = docs if docs is not None else [AI_DOC, ML_DOC]
        self.fail = fail
        self.queries: list[str] = []

    async def search(self, query: str, limit: int) -> list[Document]:
        self.queries.append(query)
        if self.fail:
            raise SearchError("boom")
        return self.docs[:limit]


class FakeLLM:
    """LLM double returning a fixed response or raising LLMError."""

    def __init__(self, response: str = "", fail: bool = False) -> None:
        self.response = response
        self.fail = fail
        self.calls: list[str] = []

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        self.calls.append(prompt)
        if self.fail:
            raise LLMError("down")
        return self.response


@pytest.fixture
def fake_search() -> FakeSearch:
    return FakeSearch()
