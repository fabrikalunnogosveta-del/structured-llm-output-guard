"""Safe path from LLM text to typed JSON."""

from .fences import strip_fences
from .parse import ParseResult, tolerant_parse
from .schema import Field, Schema, ValidationError
from .extract import ExtractResult, extract_json
from .repair import RepairLoop, RepairResult
from .breaker import CircuitBreaker, CircuitOpen

__all__ = [
    "CircuitBreaker",
    "CircuitOpen",
    "ExtractResult",
    "Field",
    "ParseResult",
    "RepairLoop",
    "RepairResult",
    "Schema",
    "ValidationError",
    "extract_json",
    "strip_fences",
    "tolerant_parse",
]

__version__ = "1.0.0"
