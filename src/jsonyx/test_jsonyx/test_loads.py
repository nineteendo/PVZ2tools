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


def test_keywords(loads: FunctionType) -> None:
    """Test JSON keywords."""
    assert loads("true") is True
    assert loads("false") is False
    assert loads("null") is None


@pytest.mark.parametrize(("input_string", "expected_result"), {
    # sign
    ("-1", -1),
    ("1", 1),

    # integer
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

    # fraction
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

    # exponent e
    ("1e1", 10.0),
    ("1E1", 10.0),

    # exponent sign
    ("1e-1", 0.1),
    ("1e1", 10.0),
    ("1e+1", 10.0),

    # exponent power
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

    # parts
    ("1", 1),
    ("1e1", 10.0),
    ("1.1", 1.1),
    ("1.1e1", 11.0),
    ("-1", -1),
    ("-1e1", -10.0),
    ("-1.1", -1.1),
    ("-1.1e1", -11.0),
})
def test_number(
    input_string: str, expected_result: float, loads: FunctionType,
) -> None:
    """Test JSON number."""
    obj: Any = loads(input_string)
    assert isinstance(obj, type(expected_result))
    assert obj == expected_result
