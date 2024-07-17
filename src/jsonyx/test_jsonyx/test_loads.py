# Copyright (C) 2024 Nice Zombies
"""JSON loads tests."""
from __future__ import annotations

__all__: list[str] = []

from math import inf, isnan, nan
from typing import TYPE_CHECKING

import pytest
from jsonyx import NAN, TRAILING_COMMA
# pylint: disable-next=W0611
from jsonyx.test_jsonyx import get_json  # type: ignore # noqa: F401
from typing_extensions import Any  # type: ignore

if TYPE_CHECKING:
    from types import ModuleType


def test_empty(json: ModuleType) -> None:
    """Test empty JSON."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads("")

    exc: Any = exc_info.value
    assert exc.msg == "Expecting value"
    assert exc.lineno == 1
    assert exc.colno == 1


@pytest.mark.parametrize(("string", "expected"), [
    ("true", True),
    ("false", False),
    ("null", None),
])
def test_keywords(json: ModuleType, string: str, expected: Any) -> None:
    """Test JSON keywords."""
    assert json.loads(string) is expected


@pytest.mark.parametrize(("string", "expected"), [
    ("NaN", nan),
    ("Infinity", inf),
    ("-Infinity", -inf),
])
def test_nan_allowed(json: ModuleType, string: str, expected: Any) -> None:
    """Test NaN if allowed."""
    obj: Any = json.loads(string, allow=NAN)
    assert isnan(obj) if isnan(expected) else obj == expected


@pytest.mark.parametrize("string", ["NaN", "Infinity", "-Infinity"])
def test_nan_not_allowed(json: ModuleType, string: str) -> None:
    """Test NaN if not allowed."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(string)

    exc: Any = exc_info.value
    assert exc.msg == f"{string} is not allowed"
    assert exc.lineno == 1
    assert exc.colno == 1


@pytest.mark.parametrize(("string", "expected"), {
    # Sign
    ("-1", -1),
    ("1", 1),

    # Integer
    ("0", 0),
    ("1", 1),
    ("2", 2),
    ("3", 3),
    ("4", 4),
    ("5", 5),
    ("6", 6),
    ("7", 7),
    ("8", 8),
    ("9", 9),
    ("10", 10),

    # Fraction
    ("1.0", 1.0),
    ("1.1", 1.1),
    ("1.2", 1.2),
    ("1.3", 1.3),
    ("1.4", 1.4),
    ("1.5", 1.5),
    ("1.6", 1.6),
    ("1.7", 1.7),
    ("1.8", 1.8),
    ("1.9", 1.9),
    ("1.01", 1.01),

    # Exponent e
    ("1e1", 10.0),
    ("1E1", 10.0),

    # Exponent sign
    ("1e-1", 0.1),
    ("1e1", 10.0),
    ("1e+1", 10.0),

    # Exponent power
    ("1e0", 1.0),
    ("1e1", 10.0),
    ("1e2", 100.0),
    ("1e3", 1000.0),
    ("1e4", 10000.0),
    ("1e5", 100000.0),
    ("1e6", 1000000.0),
    ("1e7", 10000000.0),
    ("1e8", 100000000.0),
    ("1e9", 1000000000.0),
    ("1e10", 10000000000.0),

    # Parts
    ("1", 1),
    ("1e1", 10.0),
    ("1.1", 1.1),
    ("1.1e1", 11.0),
    ("-1", -1),
    ("-1e1", -10.0),
    ("-1.1", -1.1),
    ("-1.1e1", -11.0),
})
def test_number(json: ModuleType, string: str, expected: Any) -> None:
    """Test JSON number."""
    obj: Any = json.loads(string)
    assert isinstance(obj, type(expected))
    assert obj == expected


@pytest.mark.parametrize("string", ["1e400", "-1e400"])
def test_big_number(json: ModuleType, string: str) -> None:
    """Test big JSON number."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(string)

    exc: Any = exc_info.value
    assert exc.msg == "Number is too large"
    assert exc.lineno == 1
    assert exc.colno == 1


@pytest.mark.parametrize(("string", "expected"), [
    # Empty string
    ('""', ""),

    # UTF-8
    ('"$"', "$"),
    ('"\u00a3"', "\u00a3"),
    ('"\u0418"', "\u0418"),
    ('"\u0939"', "\u0939"),
    ('"\u20ac"', "\u20ac"),
    ('"\ud55c"', "\ud55c"),
    ('"\U00010348"', "\U00010348"),
    ('"\U001096B3"', "\U001096B3"),

    # Backslash escapes
    (r'"\""', '"'),
    (r'"\\"', "\\"),
    (r'"\/"', "/"),
    (r'"\b"', "\b"),
    (r'"\f"', "\f"),
    (r'"\n"', "\n"),
    (r'"\r"', "\r"),
    (r'"\t"', "\t"),

    # Unicode escape sequences
    (r'"\u0024"', "$"),
    (r'"\u00a3"', "\u00a3"),
    (r'"\u0418"', "\u0418"),
    (r'"\u0939"', "\u0939"),
    (r'"\u20ac"', "\u20ac"),
    (r'"\ud55c"', "\ud55c"),
    (r'"\ud800"', "\ud800"),
    (r'"\ud800\udf48"', "\U00010348"),
    (r'"\udbe5\udeb3"', "\U001096B3"),

    # Multiple characters
    ('"foo"', "foo"),
    (r'"foo\/bar"', "foo/bar"),
    (r'"\ud800\u0024"', "\ud800$"),
])
def test_string(json: ModuleType, string: str, expected: Any) -> None:
    """Test JSON string."""
    assert json.loads(string) == expected


@pytest.mark.parametrize(("string", "msg", "colno"), [
    ('"', "Unterminated string", 1),
    ('"\n', "Unterminated string", 1),
    ('"\b"', "Unescaped control character", 2),
    ('"\\', "Expecting escaped character", 3),
    ('"\\\n', "Expecting escaped character", 3),
    (r'"\a"', "Invalid backslash escape", 3),
    (r'"\u"', "Expecting 4 hex digits", 4),
    (r'"\uXXXX"', "Expecting 4 hex digits", 4),
    (r'"\ud800\u"', "Expecting 4 hex digits", 10),
    (r'"\ud800\uXXXX"', "Expecting 4 hex digits", 10),
])
def test_invalid_string(
    json: ModuleType, string: str, msg: str, colno: int,
) -> None:
    """Test invalid JSON string."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(string)

    exc: Any = exc_info.value
    assert exc.msg == msg
    assert exc.lineno == 1
    assert exc.colno == colno


@pytest.mark.parametrize(("string", "expected"), [
    # Empty array
    ("[]", []),

    # One value
    ('[""]', [""]),
    ("[0]", [0]),
    ("[{}]", [{}]),
    ("[[]]", [[]]),
    ("[true]", [True]),
    ("[false]", [False]),
    ("[null]", [None]),

    # Multiple values
    ("[1, 2, 3]", [1, 2, 3]),

    # Space before delimiter
    ("[1 ,2]", [1, 2]),
])  # type: ignore
def test_array(json: ModuleType, string: str, expected: Any) -> None:
    """Test JSON array."""
    assert json.loads(string) == expected


@pytest.mark.parametrize(("string", "expected"), [
    # Empty object
    ("{}", {}),

    # TODO(Nice Zombies): add more tests
])
def test_object(json: ModuleType, string: str, expected: Any) -> None:
    """Test JSON object."""
    assert json.loads(string) == expected


@pytest.mark.parametrize(("string", "expected"), [
    ("[0,]", [0]),
    ('{"k": 0,}', {"k": 0}),
])
def test_trailing_comma_allowed(
    json: ModuleType, string: str, expected: Any,
) -> None:
    """Test trailing comma if allowed."""
    assert json.loads(string, allow=TRAILING_COMMA) == expected


@pytest.mark.parametrize(("string", "colno"), [
    ("[0,]", 3),
    ('{"k": 0,}', 8),
])
def test_trailing_comma_not_allowed(
    json: ModuleType, string: str, colno: int,
) -> None:
    """Test trailing comma if not allowed."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(string)

    exc: Any = exc_info.value
    assert exc.msg == "Trailing comma is not allowed"
    assert exc.lineno == 1
    assert exc.colno == colno


@pytest.mark.parametrize("string", ["-", "foo"])
def test_invalid_value(json: ModuleType, string: str) -> None:
    """Test invalid JSON value."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(string)

    exc: Any = exc_info.value
    assert exc.msg == "Expecting value"
    assert exc.lineno == 1
    assert exc.colno == 1
