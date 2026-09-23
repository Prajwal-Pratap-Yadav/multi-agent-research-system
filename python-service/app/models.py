"""Pydantic models shared by the API and the agent pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ResearchRequest(BaseModel):
    """Incoming research query."""

    query: str = Field(..., min_length=3, max_length=500, description="Research question.")
    max_sub_questions: int = Field(3, ge=1, le=5, description="How many sub-questions to plan.")

    @field_validator("query")
    @classmethod
    def _strip_query(cls, value: str) -> str:
        """Normalize whitespace and reject blank queries."""
        cleaned = " ".join(value.split())
        if len(cleaned) < 3:
            raise ValueError("query must contain at least 3 non-whitespace characters")
        return cleaned


class Source(BaseModel):
    """A document retrieved by the researcher agent."""

    id: int = Field(..., description="Citation number used in the report.")
    title: str
    url: str
    content: str


class Finding(BaseModel):
    """A key finding extracted by the analyst agent."""

    sub_question: str
    statement: str
    source_ids: list[int]
    score: float = Field(..., ge=0.0)


class AgentTrace(BaseModel):
    """Execution record for a single agent step."""

    agent: str
    duration_ms: float
    summary: str


class ResearchReport(BaseModel):
    """Final output of the research pipeline."""

    query: str
    sub_questions: list[str]
    findings: list[Finding]
    sources: list[Source]
    report_markdown: str
    llm_enabled: bool
    trace: list[AgentTrace]
