# Copyright (C) 2024 Nice Zombies
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

_CIRCULAR_DICT: dict[str, object] = {}
_CIRCULAR_DICT["self"] = _CIRCULAR_DICT
_CIRCULAR_LIST: list[object] = []
_CIRCULAR_LIST.append(_CIRCULAR_LIST)


class _BadDecimal(Decimal):
    def __str__(self) -> str:
        return f"_BadDecimal({super().__str__()})"


class _BadFloat(float):
    def __repr__(self) -> str:
        return f"_BadFloat({super().__repr__()})"


class _BadInt(int):
    def __repr__(self) -> str:
        return f"_BadInt({super().__repr__()})"


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


@pytest.mark.parametrize(("obj", "expected"), [
    # Empty list
    ([], "[]"),

    # One value
    ([0], "[0]"),

    # Multiple values
    ([1, 2, 3], "[1, 2, 3]"),

    # Shadow copy
    ([[]] * 3, "[[], [], []]"),
    ([{}] * 3, "[{}, {}, {}]"),
])  # type: ignore
def test_list(json: ModuleType, obj: list[object], expected: str) -> None:
    """Test list."""
    assert json.dumps(obj, end="") == expected


@pytest.mark.parametrize(("indent", "expected"), [
    (0, "[\n1,\n2,\n3\n]"),
    (1, "[\n 1,\n 2,\n 3\n]"),
    ("\t", "[\n\t1,\n\t2,\n\t3\n]"),
])
def test_list_indent(
    json: ModuleType, indent: int | str, expected: str,
) -> None:
    """Test list indent."""
    assert json.dumps([1, 2, 3], end="", indent=indent) == expected


@pytest.mark.parametrize(("obj", "expected"), [
    # Empty dict
    ({}, "{}"),

    # One value
    ({"": 0}, '{"": 0}'),

    # Multiple values
    ({"a": 1, "b": 2, "c": 3}, '{"a": 1, "b": 2, "c": 3}'),
])
def test_dict(json: ModuleType, obj: dict[str, object], expected: str) -> None:
    """Test list."""
    assert json.dumps(obj, end="") == expected


@pytest.mark.parametrize(
    "key", [0, Decimal(0), 0.0, Decimal(0.0), True, False, None],
)
def test_unserializable_key(json: ModuleType, key: object) -> None:
    """Test unserializable key."""
    with pytest.raises(TypeError, match="Keys must be str, not"):
        json.dumps({key: 0})


def test_sort_keys(json: ModuleType) -> None:
    """Test sort_keys."""
    s: str = json.dumps({"c": 3, "b": 2, "a": 1}, end="", sort_keys=True)
    assert s == '{"a": 1, "b": 2, "c": 3}'


@pytest.mark.parametrize(("indent", "expected"), [
    (0, '{\n"a": 1,\n"b": 2,\n"c": 3\n}'),
    (1, '{\n "a": 1,\n "b": 2,\n "c": 3\n}'),
    ("\t", '{\n\t"a": 1,\n\t"b": 2,\n\t"c": 3\n}'),
])
def test_dict_indent(
    json: ModuleType, indent: int | str, expected: str,
) -> None:
    """Test dict indent."""
    s: str = json.dumps({"a": 1, "b": 2, "c": 3}, end="", indent=indent)
    assert s == expected


@pytest.mark.parametrize(
    "obj", [b"", 0j, (), bytearray(), frozenset(), set()],  # type: ignore
)
def test_unserializable_value(json: ModuleType, obj: object) -> None:
    """Test unserializable value."""
    with pytest.raises(TypeError, match="is not JSON serializable"):
        json.dumps(obj)


@pytest.mark.parametrize("obj", [_CIRCULAR_DICT, _CIRCULAR_LIST])
def test_circular_reference(
    json: ModuleType, obj: dict[str, object] | list[object],
) -> None:
    """Test circular reference."""
    with pytest.raises(ValueError, match="Unexpected circular reference"):
        json.dumps(obj)


def test_default_end(json: ModuleType) -> None:
    """Test default end."""
    assert json.dumps(0) == "0\n"


def test_custom_end(json: ModuleType) -> None:
    """Test custom end."""
    assert json.dumps(0, end="") == "0"


@pytest.mark.parametrize(("obj", "expected"), [
    ([1, 2, 3], "[1,2,3]"),
    ({"a": 1, "b": 2, "c": 3}, '{"a":1,"b":2,"c":3}'),
])
def test_compact(
    json: ModuleType, obj: dict[str, object] | list[object], expected: str,
) -> None:
    """Test compact."""
    s: str = json.dumps(obj, end="", item_separator=",", key_separator=":")
    assert s == expected


@pytest.mark.parametrize(("obj", "expected"), [
    ([1, 2, 3], "[\n\t1,\n\t2,\n\t3,\n]"),
    ({"a": 1, "b": 2, "c": 3}, '{\n\t"a": 1,\n\t"b": 2,\n\t"c": 3,\n}'),
])
def test_trailing_comma_indent(
    json: ModuleType, obj: dict[str, object] | list[object], expected: str,
) -> None:
    """Test trailing_comma with indent."""
    s: str = json.dumps(obj, end="", indent="\t", trailing_comma=True)
    assert s == expected


@pytest.mark.parametrize(("obj", "expected"), [
    ([1, 2, 3], "[1, 2, 3]"),
    ({"a": 1, "b": 2, "c": 3}, '{"a": 1, "b": 2, "c": 3}'),
])
def test_trailing_comma_no_indent(
    json: ModuleType, obj: dict[str, object] | list[object], expected: str,
) -> None:
    """Test trailing_comma without indent."""
    assert json.dumps(obj, end="", trailing_comma=True) == expected
