# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): add more tests
"""JSON dumps tests."""
from __future__ import annotations

__all__: list[str] = []

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from jsonyx.allow import NAN_AND_INFINITY, SURROGATES
# pylint: disable-next=W0611
from jsonyx.test import get_json  # type: ignore # noqa: F401

if TYPE_CHECKING:
    from types import ModuleType


class _BadDecimal(Decimal):
    def __str__(self) -> str:
        return repr(self)


class _BadFloat(float):
    def __str__(self) -> str:
        return repr(self)


class _BadInt(int):
    def __str__(self) -> str:
        return repr(self)


@pytest.mark.parametrize(("obj", "expected"), [
    (True, "true"),
    (False, "false"),
    (None, "null"),
])
def test_singletons(
    json: ModuleType, obj: bool | None, expected: str,  # noqa: FBT001
) -> None:
    """Test singletons."""
    assert json.dumps(obj, end="") == expected


@pytest.mark.parametrize("num", [0, 1])
@pytest.mark.parametrize("num_type", [_BadDecimal, _BadInt, Decimal, int])
def test_int(
    json: ModuleType, num: int, num_type: type[Decimal | int],
) -> None:
    """Test integer."""
    assert json.dumps(num_type(num), end="") == repr(num)


@pytest.mark.parametrize("num_type", [_BadDecimal, _BadFloat, Decimal, float])
def test_rational_number(
    json: ModuleType, num_type: type[Decimal | float],
) -> None:
    """Test rational number."""
    assert json.dumps(num_type("0.0"), end="") == "0.0"


@pytest.mark.parametrize("num", ["NaN", "Infinity", "-Infinity"])
@pytest.mark.parametrize("num_type", [_BadDecimal, _BadFloat, Decimal, float])
def test_nan_and_infinity(
    json: ModuleType, num: str, num_type: type[Decimal | float],
) -> None:
    """Test NaN and infinity."""
    assert json.dumps(num_type(num), allow=NAN_AND_INFINITY, end="") == num


@pytest.mark.parametrize("num", ["NaN", "Infinity", "-Infinity"])
@pytest.mark.parametrize("num_type", [_BadDecimal, _BadFloat, Decimal, float])
def test_nan_and_infinity_not_allowed(
    json: ModuleType, num: str, num_type: type[Decimal | float],
) -> None:
    """Test NaN and infinity if not allowed."""
    with pytest.raises(ValueError, match="is not allowed"):
        json.dumps(num_type(num))


@pytest.mark.parametrize("num", ["NaN2", "-NaN", "-NaN2"])
@pytest.mark.parametrize("num_type", [_BadDecimal, Decimal])
def test_nan_payload(
    json: ModuleType, num: str, num_type: type[Decimal],
) -> None:
    """Test NaN payload."""
    assert json.dumps(num_type(num), allow=NAN_AND_INFINITY, end="") == "NaN"


@pytest.mark.parametrize("num", ["NaN2", "-NaN", "-NaN2"])
@pytest.mark.parametrize("num_type", [_BadDecimal, Decimal])
def test_nan_payload_not_allowed(
    json: ModuleType, num: str, num_type: type[Decimal],
) -> None:
    """Test NaN payload if not allowed."""
    with pytest.raises(ValueError, match="is not allowed"):
        json.dumps(num_type(num))


@pytest.mark.parametrize("num_type", [_BadDecimal, Decimal])
def test_signaling_nan(json: ModuleType, num_type: type[Decimal]) -> None:
    """Test signaling NaN."""
    with pytest.raises(ValueError, match="is not JSON serializable"):
        json.dumps(num_type("sNaN"))


@pytest.mark.parametrize(("obj", "expected"), [
    # Empty string
    ("", '""'),

    # Control characters
    ("\x00", r'"\u0000"'),
    ("\x08", r'"\b"'),
    ("\t", r'"\t"'),
    ("\n", r'"\n"'),
    ("\x0c", r'"\f"'),
    ("\r", r'"\r"'),
    ('"', r'"\""'),
    ("\\", r'"\\"'),

    # UTF-8
    ("$", '"$"'),
    ("\xa3", '"\u00a3"'),
    ("\u0418", '"\u0418"'),
    ("\u0939", '"\u0939"'),
    ("\u20ac", '"\u20ac"'),
    ("\ud55c", '"\ud55c"'),
    ("\U00010348", '"\U00010348"'),
    ("\U001096b3", '"\U001096b3"'),

    # Surrogates
    ("\ud800", '"\ud800"'),
    ("\udf48", '"\udf48"'),  # noqa: PT014

    # Multiple characters
    ("foo", '"foo"'),
    (r"foo\bar", r'"foo\\bar"'),
])
def test_string(json: ModuleType, obj: str, expected: str) -> None:
    """Test string."""
    assert json.dumps(obj, end="") == expected


@pytest.mark.parametrize(("obj", "expected"), [
    ("\xa3", r'"\u00a3"'),
    ("\u0418", r'"\u0418"'),
    ("\u0939", r'"\u0939"'),
    ("\u20ac", r'"\u20ac"'),
    ("\ud55c", r'"\ud55c"'),
    ("\U00010348", r'"\ud800\udf48"'),
    ("\U001096b3", r'"\udbe5\udeb3"'),
])
def test_ensure_ascii(json: ModuleType, obj: str, expected: str) -> None:
    """Test ensure_ascii."""
    assert json.dumps(obj, end="", ensure_ascii=True) == expected


@pytest.mark.parametrize(("obj", "expected"), [
    ("\ud800", r'"\ud800"'),
    ("\udf48", r'"\udf48"'),
])
def test_surrogate_escapes(json: ModuleType, obj: str, expected: str) -> None:
    """Test surrogate escapes."""
    s: str = json.dumps(obj, allow=SURROGATES, end="", ensure_ascii=True)
    assert s == expected


@pytest.mark.parametrize("obj", ["\ud800", "\udf48"])  # noqa: PT014
def test_surrogate_escapes_not_allowed(json: ModuleType, obj: str) -> None:
    """Test surrogate escapes if not allowed."""
    with pytest.raises(ValueError, match="Surrogates are not allowed"):
        json.dumps(obj, ensure_ascii=True)
