"""Minimal async client for the Anthropic Messages API."""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from app.errors import LLMError

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class LLMClient(Protocol):
    """Anything that can turn a prompt into text."""

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        """Return the model's text response for ``prompt``."""
        ...


class AnthropicClient:
    """LLM client backed by Claude via the Messages API."""

    def __init__(self, http: httpx.AsyncClient, api_key: str, model: str) -> None:
        """Create a client using a shared ``httpx.AsyncClient``."""
        self._http = http
        self._api_key = api_key
        self._model = model

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        """Send a single-turn request and return concatenated text blocks.

        Raises:
            LLMError: on transport failures, non-2xx responses or empty output.
        """
        try:
            response = await self._http.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc
        if response.status_code >= 400:
            raise LLMError(f"LLM returned HTTP {response.status_code}: {response.text[:200]}")
        blocks = response.json().get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
        if not text:
            raise LLMError("LLM returned an empty response")
        logger.debug("llm_completion", extra={"model": self._model, "chars": len(text)})
        return text
