"""Domain exceptions raised by the research pipeline."""


class ResearchError(Exception):
    """Base class for all pipeline errors."""


class SearchError(ResearchError):
    """Raised when the search backend fails or returns malformed data."""


class LLMError(ResearchError):
    """Raised when the LLM provider fails or returns an unusable response."""
