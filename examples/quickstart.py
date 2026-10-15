"""Quickstart — LLM text → typed JSON (no external services)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm_output_guard import Field, RepairLoop, Schema, extract_json


def main() -> None:
    schema = Schema(
        fields={
            "title": Field(str),
            "score": Field(int, min_value=0, max_value=100),
            "tags": Field(list, optional=True),
        }
    )

    raw = '''Sure! Here is the JSON:
```json
{"title": "Hello", "score": 42,}
```'''
    result = extract_json(raw, schema)
    print("extract:", result.ok, result.value)

    calls = {"n": 0}

    def call(err=None):
        calls["n"] += 1
        return '{"title": "Hello", "score": "high"}' if calls["n"] == 1 else '{"title": "Hello", "score": 42}'

    repaired = RepairLoop(schema=schema, max_attempts=3).run(call)
    print("repair:", repaired.ok, "attempts=", repaired.attempts, "errors=", repaired.errors)


if __name__ == "__main__":
    main()
