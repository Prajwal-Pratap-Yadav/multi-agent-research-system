"""Search providers used by the researcher agent."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.errors import SearchError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Document:
    """A raw search hit before citation numbering."""

    title: str
    url: str
    content: str


class SearchProvider(Protocol):
    """Anything that can return documents for a query."""

    async def search(self, query: str, limit: int) -> list[Document]:
        """Return up to ``limit`` documents relevant to ``query``."""
        ...


class WikipediaSearchProvider:
    """Search provider backed by the public MediaWiki API (no API key required)."""

    def __init__(self, http: httpx.AsyncClient, base_url: str) -> None:
        """Create a provider that issues requests through ``http``."""
        self._http = http
        self._base_url = base_url

    async def search(self, query: str, limit: int) -> list[Document]:
        """Run a full-text search and return plain-text intro extracts.

        Raises:
            SearchError: if the API is unreachable or returns an unexpected payload.
        """
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": str(limit),
            "prop": "extracts|info",
            "exintro": "1",
            "explaintext": "1",
            "inprop": "url",
            "redirects": "1",
        }
        try:
            response = await self._http.get(self._base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SearchError(f"Search request failed for {query!r}: {exc}") from exc

        pages = payload.get("query", {}).get("pages", {})
        if not isinstance(pages, dict):
            raise SearchError("Unexpected search response shape")
        ordered = sorted(pages.values(), key=lambda p: p.get("index", 0))
        documents = [
            Document(title=p["title"], url=p.get("fullurl", ""), content=p.get("extract", ""))
            for p in ordered
            if p.get("title") and p.get("extract")
        ]
        logger.info("search_completed", extra={"query": query, "hits": len(documents)})
        return documents
