"""Tolerant JSON parse — handle common LLM artifacts without throwing."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from .fences import strip_fences

_SMART_QUOTES = {
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
}
_TRAILING_COMMA = re.compile(r",\s*([}\]])")
_LINE_COMMENT = re.compile(r"^\s*//.*$", re.MULTILINE)


@dataclass(frozen=True)
class ParseResult:
    ok: bool
    value: Any = None
    error: Optional[str] = None


def _normalize(text: str) -> str:
    out = strip_fences(text)
    for bad, good in _SMART_QUOTES.items():
        out = out.replace(bad, good)
    out = _TRAILING_COMMA.sub(r"\1", out)
    out = _LINE_COMMENT.sub("", out)
    return out.strip()


def tolerant_parse(text: str) -> ParseResult:
    """Parse LLM text to Python objects. Never raises."""
    if not isinstance(text, str) or not text.strip():
        return ParseResult(ok=False, error="empty_input")
    candidate = _normalize(text)
    if not candidate:
        return ParseResult(ok=False, error="empty_after_strip")
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return ParseResult(ok=False, error=f"invalid_json: {exc.msg} at pos {exc.pos}")
    return ParseResult(ok=True, value=value)
