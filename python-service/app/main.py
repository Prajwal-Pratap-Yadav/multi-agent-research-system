"""FastAPI entrypoint for the research agent service."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app import __version__
from app.agents import AnalystAgent, PlannerAgent, ResearcherAgent, WriterAgent
from app.config import Settings
from app.errors import ResearchError, SearchError
from app.llm import AnthropicClient, LLMClient
from app.logging_config import configure_logging
from app.models import ResearchReport, ResearchRequest
from app.orchestrator import ResearchOrchestrator
from app.search import SearchProvider, WikipediaSearchProvider

logger = logging.getLogger(__name__)

USER_AGENT = f"multi-agent-research-system/{__version__} (https://github.com)"


def build_orchestrator(
    settings: Settings, search: SearchProvider, llm: LLMClient | None
) -> ResearchOrchestrator:
    """Wire the default four-agent pipeline."""
    agents = [
        PlannerAgent(llm),
        ResearcherAgent(search, settings.max_sources_per_question),
        AnalystAgent(),
        WriterAgent(llm),
    ]
    return ResearchOrchestrator(agents, llm_enabled=llm is not None)


def create_app(
    settings: Settings | None = None, orchestrator: ResearchOrchestrator | None = None
) -> FastAPI:
    """Application factory; ``orchestrator`` may be injected for testing."""
    settings = settings or Settings.from_env()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if orchestrator is not None:
            app.state.orchestrator = orchestrator
            yield
            return
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, headers={"User-Agent": USER_AGENT}
        ) as http:
            llm = (
                AnthropicClient(http, settings.anthropic_api_key, settings.anthropic_model)
                if settings.anthropic_api_key
                else None
            )
            search = WikipediaSearchProvider(http, settings.search_base_url)
            app.state.orchestrator = build_orchestrator(settings, search, llm)
            logger.info("service_started", extra={"llm_enabled": llm is not None})
            yield

    app = FastAPI(title="Research Agent Service", version=__version__, lifespan=lifespan)

    @app.middleware("http")
    async def request_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response

    @app.exception_handler(SearchError)
    async def search_error_handler(_: Request, exc: SearchError) -> JSONResponse:
        logger.error("search_unavailable", extra={"error": str(exc)})
        return JSONResponse(status_code=502, content={"detail": "Search backend unavailable"})

    @app.exception_handler(ResearchError)
    async def research_error_handler(_: Request, exc: ResearchError) -> JSONResponse:
        logger.error("research_failed", extra={"error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "Research pipeline failed"})

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok", "version": __version__}

    @app.post("/research", response_model=ResearchReport)
    async def research(body: ResearchRequest, request: Request) -> ResearchReport:
        """Run the multi-agent pipeline for ``body.query``."""
        pipeline: ResearchOrchestrator = request.app.state.orchestrator
        return await pipeline.run(body)

    return app


app = create_app()
