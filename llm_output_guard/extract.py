"""One entry point: LLM text → validated dict."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .parse import tolerant_parse
from .schema import Schema, ValidationError


@dataclass(frozen=True)
class ExtractResult:
    ok: bool
    value: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def extract_json(text: str, schema: Optional[Schema] = None) -> ExtractResult:
    """Strip fences → tolerant parse → optional schema validate."""
    parsed = tolerant_parse(text)
    if not parsed.ok:
        return ExtractResult(ok=False, error=parsed.error)
    value = parsed.value
    if schema is None:
        if not isinstance(value, dict):
            return ExtractResult(ok=False, error="not_a_json_object")
        return ExtractResult(ok=True, value=value)
    try:
        validated = schema.validate(value)
    except ValidationError as exc:
        return ExtractResult(ok=False, error=str(exc))
    return ExtractResult(ok=True, value=validated)
