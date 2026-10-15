"""Behavioral contracts — fences, tolerant parse, schema, repair, breaker."""

from llm_output_guard import (
    CircuitBreaker,
    CircuitOpen,
    Field,
    RepairLoop,
    Schema,
    ValidationError,
    extract_json,
    strip_fences,
    tolerant_parse,
)

SCHEMA = Schema(
    fields={
        "title": Field(str),
        "score": Field(int, min_value=0, max_value=100),
        "tags": Field(list, optional=True),
    }
)


def test_strip_fences():
    raw = '```json\n{"a": 1}\n```'
    assert strip_fences(raw) == '{"a": 1}'
    raw2 = "Sure! Here's the JSON:\n{\"a\": 1}"
    assert strip_fences(raw2) == '{"a": 1}'


def test_tolerant_parse_smart_quotes():
    r = tolerant_parse('{“a”: 1}')
    assert r.ok
    assert r.value == {"a": 1}


def test_tolerant_parse_trailing_comma():
    r = tolerant_parse('{"a": 1,}')
    assert r.ok
    assert r.value == {"a": 1}


def test_tolerant_parse_rejects_garbage():
    r = tolerant_parse("not json at all")
    assert not r.ok


def test_extract_json_with_schema_ok():
    raw = '```json\n{"title": "Hi", "score": 42}\n```'
    r = extract_json(raw, SCHEMA)
    assert r.ok
    assert r.value == {"title": "Hi", "score": 42}


def test_extract_json_wrong_type():
    r = extract_json('{"title": "Hi", "score": "high"}', SCHEMA)
    assert not r.ok
    assert "expected_int" in (r.error or "")


def test_extract_json_missing_field():
    r = extract_json('{"title": "Hi"}', SCHEMA)
    assert not r.ok
    assert "missing_field:score" in (r.error or "")


def test_extract_json_extra_field_rejected():
    r = extract_json('{"title": "Hi", "score": 1, "junk": true}', SCHEMA)
    assert not r.ok


def test_repair_loop_heals():
    calls = {"n": 0}

    def call(err=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return '{"title": "Hi", "score": "high"}'
        return '{"title": "Hi", "score": 42}'

    result = RepairLoop(schema=SCHEMA, max_attempts=3).run(call)
    assert result.ok
    assert result.attempts == 2
    assert result.value["score"] == 42


def test_repair_loop_exhausts():
    result = RepairLoop(schema=SCHEMA, max_attempts=2).run(lambda err=None: '{"title": "Hi"}')
    assert not result.ok
    assert result.attempts == 2


def test_circuit_breaker():
    clock = {"t": 0.0}
    cb = CircuitBreaker(failures=2, cooldown_s=300, clock=lambda: clock["t"])
    for _ in range(2):
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
        except RuntimeError:
            pass
    assert not cb.allow()
    try:
        cb.call(lambda: 1)
        raise AssertionError("should be open")
    except CircuitOpen:
        pass
    clock["t"] = 400.0
    assert cb.state.value == "half_open"
    cb.record_success()
    assert cb.allow()


def test_schema_min_max():
    s = Schema(fields={"n": Field(int, min_value=0, max_value=10)})
    assert s.validate({"n": 5}) == {"n": 5}
    try:
        s.validate({"n": 99})
        raise AssertionError("should fail")
    except ValidationError as exc:
        assert "above_max" in str(exc)
