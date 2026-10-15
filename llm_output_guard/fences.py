"""Strip markdown fences and leading prose from LLM text."""

from __future__ import annotations

import re

_FENCE = re.compile(r"```(?:json|JSON|javascript|js)?\s*\n(.*?)\n\s*```", re.DOTALL)
_PROSE_PREFIX = re.compile(
    r"^(?:sure|here(?:'s| is)|of course|certainly|ok(?:ay)?)[^{}\[]*",
    re.IGNORECASE | re.DOTALL,
)


def strip_fences(text: str) -> str:
    """Remove ```json fences and common lead-in prose."""
    if not isinstance(text, str):
        return ""
    out = text.strip()
    m = _FENCE.search(out)
    if m:
        return m.group(1).strip()
    out = _PROSE_PREFIX.sub("", out).strip()
    return out
