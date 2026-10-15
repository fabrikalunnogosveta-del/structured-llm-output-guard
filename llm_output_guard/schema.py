"""Declarative type contracts for LLM JSON payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type, Union


class ValidationError(Exception):
    """Raised when a payload fails the schema contract."""


@dataclass(frozen=True)
class Field:
    """A single typed field contract."""

    type: Union[Type, tuple, Sequence[Type]]
    optional: bool = False
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    choices: Optional[Sequence[Any]] = None


@dataclass
class Schema:
    """Declarative schema: required fields, types, bounds, enum choices."""

    fields: Dict[str, Field] = field(default_factory=dict)
    allow_extra: bool = False

    def validate(self, payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError(f"payload_not_object: {type(payload).__name__}")
        out: Dict[str, Any] = {}
        errors: List[str] = []
        for name, spec in self.fields.items():
            if name not in payload:
                if spec.optional:
                    if spec.default is not None:
                        out[name] = spec.default
                    continue
                errors.append(f"missing_field:{name}")
                continue
            raw = payload[name]
            try:
                out[name] = _coerce_check(name, raw, spec)
            except ValidationError as exc:
                errors.append(str(exc))
        if not self.allow_extra:
            extra = set(payload) - set(self.fields)
            if extra:
                errors.append(f"extra_fields:{','.join(sorted(extra))}")
        if errors:
            raise ValidationError(";".join(errors))
        return out


def _coerce_check(name: str, value: Any, spec: Field) -> Any:
    expected = spec.type
    if expected is list:
        if not isinstance(value, list):
            raise ValidationError(f"{name}:expected_list")
    elif expected is dict:
        if not isinstance(value, dict):
            raise ValidationError(f"{name}:expected_dict")
    elif isinstance(expected, tuple):
        if not isinstance(value, expected):
            raise ValidationError(f"{name}:expected_{'|'.join(t.__name__ for t in expected)}")
    elif expected is bool:
        if not isinstance(value, bool):
            raise ValidationError(f"{name}:expected_bool")
    elif expected is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(f"{name}:expected_int")
    elif expected is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"{name}:expected_float")
        value = float(value)
    elif expected is str:
        if not isinstance(value, str):
            raise ValidationError(f"{name}:expected_str")
    elif isinstance(expected, type):
        if not isinstance(value, expected):
            raise ValidationError(f"{name}:expected_{expected.__name__}")
    if spec.choices is not None and value not in spec.choices:
        raise ValidationError(f"{name}:invalid_choice")
    if spec.min_value is not None and isinstance(value, (int, float)) and value < spec.min_value:
        raise ValidationError(f"{name}:below_min")
    if spec.max_value is not None and isinstance(value, (int, float)) and value > spec.max_value:
        raise ValidationError(f"{name}:above_max")
    return value
