# Copyright (C) 2024 Nice Zombies
"""JSON loads tests."""
from __future__ import annotations

__all__: list[str] = []

from typing import TYPE_CHECKING

import pytest
# pylint: disable-next=W0611
from jsonyx.test_jsonyx import get_json  # type: ignore # noqa: F401
from typing_extensions import Any

if TYPE_CHECKING:
    from types import FunctionType, ModuleType


@pytest.fixture(name="loads")
def get_loads(json: ModuleType) -> FunctionType:
    """Get JSON loads."""
    return json.loads


@pytest.mark.parametrize(("string", "expected"), [
    ("true", True),
    ("false", False),
    ("null", None),
])
def test_keywords(loads: FunctionType, string: str, expected: Any) -> None:
    """Test JSON keywords."""
    assert loads(string) is expected


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
def test_number(loads: FunctionType, string: str, expected: Any) -> None:
    """Test JSON number."""
    obj: Any = loads(string)
    assert isinstance(obj, type(expected))
    assert obj == expected


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
def test_string(loads: FunctionType, string: str, expected: Any) -> None:
    """Test JSON string."""
    assert loads(string) == expected


@pytest.mark.parametrize(("string", "expected"), [
    # Empty array
    ("[]", []),

    # TODO(Nice Zombies): add more tests
])
def test_array(loads: FunctionType, string: str, expected: Any) -> None:
    """Test JSON array."""
    assert loads(string) == expected


@pytest.mark.parametrize(("string", "expected"), [
    # Empty object
    ("{}", {}),

    # TODO(Nice Zombies): add more tests
])
def test_object(loads: FunctionType, string: str, expected: Any) -> None:
    """Test JSON object."""
    assert loads(string) == expected
