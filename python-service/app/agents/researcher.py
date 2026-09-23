"""Researcher agent: gathers source documents for each sub-question."""

from __future__ import annotations

import asyncio
import logging

from app.agents.base import Agent, ResearchContext
from app.errors import SearchError
from app.models import Source
from app.search import Document, SearchProvider
from app.text import keywords

logger = logging.getLogger(__name__)


class ResearcherAgent(Agent):
    """Searches concurrently for every sub-question and de-duplicates results by URL."""

    name = "researcher"

    def __init__(self, search: SearchProvider, max_sources_per_question: int) -> None:
        """Create a researcher bound to a search provider."""
        super().__init__(llm=None)
        self._search = search
        self._limit = max_sources_per_question

    async def run(self, ctx: ResearchContext) -> str:
        """Populate ``ctx.sources``.

        Individual search failures are logged and skipped; if *every* search fails the
        last error is re-raised so the caller can report an upstream outage.
        """
        results = await asyncio.gather(
            *(self._search_one(q) for q in ctx.sub_questions), return_exceptions=True
        )
        errors = [r for r in results if isinstance(r, BaseException)]
        if errors and len(errors) == len(results):
            raise SearchError("All searches failed") from errors[-1]

        seen: set[str] = set()
        sources: list[Source] = []
        for batch in results:
            if isinstance(batch, BaseException):
                continue
            for doc in batch:
                key = doc.url or doc.title
                if key in seen:
                    continue
                seen.add(key)
                sources.append(
                    Source(id=len(sources) + 1, title=doc.title, url=doc.url, content=doc.content)
                )
        ctx.sources = sources
        return f"Collected {len(sources)} unique sources ({len(errors)} failed searches)"

    async def _search_one(self, question: str) -> list[Document]:
        """Search using the question's keywords, which works better than full sentences."""
        terms = " ".join(keywords(question)) or question
        try:
            return await self._search.search(terms, self._limit)
        except SearchError as exc:
            logger.warning("search_failed", extra={"sub_question": question, "error": str(exc)})
            raise
