"""Circuit breaker — stop hammering a failing LLM/API."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, TypeVar

T = TypeVar("T")


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpen(RuntimeError):
    """Raised when the circuit is open and calls are rejected."""


@dataclass
class CircuitBreaker:
    failures: int = 5
    cooldown_s: float = 300.0
    clock: Callable[[], float] = time.monotonic
    _fail_count: int = field(default=0, init=False, repr=False)
    _state: State = field(default=State.CLOSED, init=False, repr=False)
    _opened_at: float = field(default=0.0, init=False, repr=False)

    @property
    def state(self) -> State:
        if self._state == State.OPEN:
            if self.clock() - self._opened_at >= self.cooldown_s:
                self._state = State.HALF_OPEN
        return self._state

    def allow(self) -> bool:
        return self.state != State.OPEN

    def record_success(self) -> None:
        self._fail_count = 0
        self._state = State.CLOSED

    def record_failure(self) -> None:
        self._fail_count += 1
        if self._fail_count >= self.failures:
            self._state = State.OPEN
            self._opened_at = self.clock()

    def call(self, fn: Callable[[], T]) -> T:
        if not self.allow():
            raise CircuitOpen(f"circuit open for {self.cooldown_s}s")
        try:
            result = fn()
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result
