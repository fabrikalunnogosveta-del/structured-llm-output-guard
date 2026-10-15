"""Repair loop — re-prompt with the exact validation error."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from .extract import extract_json
from .schema import Schema


@dataclass
class RepairResult:
    ok: bool
    value: Optional[dict] = None
    attempts: int = 0
    errors: List[str] = field(default_factory=list)


class RepairLoop:
    """On validation failure, call again with the error message."""

    def __init__(self, schema: Optional[Schema] = None, max_attempts: int = 3):
        self.schema = schema
        self.max_attempts = max_attempts

    def run(self, call: Callable[[Optional[str]], str]) -> RepairResult:
        errors: List[str] = []
        for attempt in range(1, self.max_attempts + 1):
            err = errors[-1] if errors else None
            raw = call(err)
            result = extract_json(raw, self.schema)
            if result.ok:
                return RepairResult(ok=True, value=result.value, attempts=attempt, errors=errors)
            errors.append(result.error or "validation_failed")
        return RepairResult(ok=False, attempts=self.max_attempts, errors=errors)
