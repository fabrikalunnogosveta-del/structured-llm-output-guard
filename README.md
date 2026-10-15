# structured-llm-output-guard

**One safe path from LLM text to typed JSON — schema validation, repair loop, and circuit breaker.**

**This is the solution, not the problem.** In production multi-agent pipelines, structured LLM output is the only JSON path (60+ contracts, 83 call sites). This repo is that pattern as a standalone library.

[![CI](https://github.com/fabrikalunnogosveta-del/structured-llm-output-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/fabrikalunnogosveta-del/structured-llm-output-guard/actions)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen)

---

## The problem we solved

**`json.loads(llm_text)` is a trap.** LLMs do not return JSON — they return *text that looks like JSON*.

```python
json.loads(llm_response)  # 💥
```

LLMs do not return JSON. They return **text that sometimes looks like JSON**:

| Failure mode | What you see |
|---|---|
| Markdown fences | ```` ```json\n{...}\n``` ```` |
| Extra commentary | `Sure! Here's the JSON: {...}` |
| Truncation | `{"name": "Alice", "role":` |
| Soft corruption | trailing commas, smart quotes, comments |
| Confident garbage | valid JSON with wrong schema |

`json.loads` throws (or worse: silently parses the wrong shape).
This library makes LLM → JSON a **contract**, not a hope.

---

## Architecture

```
LLM response (str)
      │
      ▼
┌─────────────────┐
│  strip_fences   │  remove ```json ... ```
└────────┬────────┘
         ▼
┌─────────────────┐
│  parse_json     │  tolerant JSON parse (no json.loads on raw)
└────────┬────────┘
         ▼
┌─────────────────┐
│  validate       │  typed schema / required fields / types
└────────┬────────┘
   pass  │  fail
   ┌─────┴─────┐
   ▼           ▼
 return    RepairLoop
           (re-prompt with exact error)
                │
                ▼
        CircuitBreaker
        (don't hammer a dead API)
```

---

## What you get

| Component | What it does |
|---|---|
| `strip_fences` | Remove markdown code fences and leading prose |
| `tolerant_parse` | Parse JSON without throwing on common LLM artifacts |
| `Schema` / `Field` | Declarative type contracts (str, int, bool, list, dict, enum) |
| `validate_payload` | Check types, required fields, extra-field policy |
| `RepairLoop` | On failure → call again with the **exact validation error** |
| `CircuitBreaker` | N failures → cooldown → auto-reset |
| `extract_json` | One entry point: text → validated dict |

---

## How this maps to real jobs

| Job title | What this repo proves |
|---|---|
| **LLM / AI Systems Engineer** | production-safe LLM output contracts |
| **AI Reliability / LLM Ops** | repair loop + circuit breaker |
| **Prompt Systems Engineer** | schema-first prompting with error feedback |
| **Backend / Python Engineer** | typed contracts, fail-closed parsing |

---

## Install

```bash
git clone https://github.com/fabrikalunnogosveta-del/structured-llm-output-guard.git
cd structured-llm-output-guard
pip install -r requirements.txt
```

## Quickstart

```python
from llm_output_guard import Schema, Field, extract_json, RepairLoop, CircuitBreaker

schema = Schema(
    fields={
        "title": Field(str),
        "score": Field(int, min_value=0, max_value=100),
        "tags": Field(list, optional=True),
    }
)

# One-shot extract
raw = '''```json
{"title": "Hello", "score": 42}
```'''
result = extract_json(raw, schema)
assert result.ok
assert result.value["score"] == 42

# Self-healing repair loop
def call_model(err=None):
    if err:
        return '{"title": "Hello", "score": 42}'  # fixed
    return '{"title": "Hello", "score": "high"}'  # wrong type

loop = RepairLoop(schema=schema, max_attempts=3)
repaired = loop.run(call_model)
assert repaired.ok
assert repaired.attempts == 2  # healed on 2nd try

# Circuit breaker
breaker = CircuitBreaker(failures=5, cooldown_s=300)
```

---

## Testing philosophy

Tests prove **behavioral contracts**:
- markdown fences are stripped before parse
- smart quotes / trailing commas handled
- wrong type → repair loop heals
- missing required field → exact error message
- circuit opens after N failures
- truncation detection (`finish_reason="length"` pattern)

```bash
python -m pytest tests/ -q
```

---

## Production context

Extracted from a multi-agent production platform where **Instructor-style structured
output was the only JSON path** (60+ Pydantic contracts, 83 call sites, C1–C7 gates).

This repo is the **standalone core** — no vendor lock-in, no secrets.

---

## Related

- [guards-and-laws](https://github.com/fabrikalunnogosveta-del/guards-and-laws) — quality gates, domain laws, anti-hallucination
- [humanlike-browser-engine](https://github.com/fabrikalunnogosveta-del/humanlike-browser-engine) — human-like browser motion

---

## License

MIT

---

## Author

**Maxim Parshshin** — AI/LLM systems, quality gates, browser automation.
Remote contracts.
