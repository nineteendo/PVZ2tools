# Copyright (C) 2024 Nice Zombies
"""JSON loads tests."""
from __future__ import annotations

__all__: list[str] = []

from decimal import Decimal
from math import inf, isnan, nan
from typing import TYPE_CHECKING

import pytest
from jsonyx.allow import (
    COMMENTS, DUPLICATE_KEYS, MISSING_COMMAS, NAN_AND_INFINITY, SURROGATES,
    TRAILING_COMMA,
)
# pylint: disable-next=W0611
from jsonyx.test_jsonyx import get_json  # type: ignore # noqa: F401
from typing_extensions import Any  # type: ignore

if TYPE_CHECKING:
    from types import ModuleType


def _check_syntax_err(
    exc_info: pytest.ExceptionInfo[Any], msg: str, colno: int,
    end_colno: int = 0,
) -> None:
    exc: Any = exc_info.value
    if not end_colno:
        end_colno = colno

    assert exc.msg == msg
    assert exc.lineno == 1
    assert exc.end_lineno == 1
    assert exc.colno == colno
    assert exc.end_colno == end_colno


def test_utf8_bom(json: ModuleType) -> None:
    """Test UTF-8 BOM."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads("\ufeff0")

    _check_syntax_err(exc_info, "Unexpected UTF-8 BOM", 1)


@pytest.mark.parametrize(("s", "expected"), [
    ("true", True),
    ("false", False),
    ("null", None),
])
def test_keywords(json: ModuleType, s: str, expected: Any) -> None:
    """Test JSON keywords."""
    assert json.loads(s) is expected


@pytest.mark.parametrize(("s", "expected"), [
    ("NaN", Decimal("NaN")),
    ("Infinity", Decimal("Infinity")),
    ("-Infinity", Decimal("-Infinity")),
])
def test_nan_and_infinity_decimal(
    json: ModuleType, s: str, expected: Any,
) -> None:
    """Test NaN and infinity with decimal."""
    obj: Any = json.loads(s, allow=NAN_AND_INFINITY, use_decimal=True)
    assert isinstance(obj, Decimal)
    if isnan(expected):
        assert isnan(obj)
    else:
        assert obj == expected


@pytest.mark.parametrize(("s", "expected"), [
    ("NaN", nan),
    ("Infinity", inf),
    ("-Infinity", -inf),
])
def test_nan_and_infinity_float(
    json: ModuleType, s: str, expected: Any,
) -> None:
    """Test NaN and infinity with float."""
    obj: Any = json.loads(s, allow=NAN_AND_INFINITY)
    assert isinstance(obj, float)
    if isnan(expected):
        assert isnan(obj)
    else:
        assert obj == expected


@pytest.mark.parametrize("s", ["NaN", "Infinity", "-Infinity"])
def test_nan_and_infinity_not_allowed(json: ModuleType, s: str) -> None:
    """Test NaN and infinity if not allowed."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s)

    _check_syntax_err(exc_info, f"{s} is not allowed", 1, len(s) + 1)


@pytest.mark.parametrize(("s", "expected"), {
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
def test_number(json: ModuleType, s: str, expected: Any) -> None:
    """Test JSON number."""
    obj: Any = json.loads(s)
    assert isinstance(obj, type(expected))
    assert obj == expected


@pytest.mark.parametrize(("s", "expected"), [
    ("1e400", Decimal("1E+400")),
    ("-1e400", Decimal("-1E+400")),
])
def test_big_number_decimal(json: ModuleType, s: str, expected: Any) -> None:
    """Test big JSON number with decimal."""
    assert json.loads(s, use_decimal=True) == expected


@pytest.mark.parametrize("s", ["1e400", "-1e400"])
def test_big_number_float(json: ModuleType, s: str) -> None:
    """Test big JSON number with float."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s)

    _check_syntax_err(exc_info, "Big numbers require decimal", 1, len(s) + 1)


@pytest.mark.parametrize("s", [
    "1e1000000000000000000", "-1e1000000000000000000",
])
def test_huge_number(json: ModuleType, s: str) -> None:
    """Test huge JSON number with decimal."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s, use_decimal=True)

    _check_syntax_err(exc_info, "Number is too big", 1, len(s) + 1)


@pytest.mark.parametrize(("s", "expected"), [
    # Empty string
    ('""', ""),

    # UTF-8
    ('"$"', "$"),
    ('"\u00a3"', "\xa3"),
    ('"\u0418"', "\u0418"),
    ('"\u0939"', "\u0939"),
    ('"\u20ac"', "\u20ac"),
    ('"\ud55c"', "\ud55c"),
    ('"\U00010348"', "\U00010348"),
    ('"\U001096b3"', "\U001096b3"),

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
    (r'"\u00a3"', "\xa3"),
    (r'"\u0418"', "\u0418"),
    (r'"\u0939"', "\u0939"),
    (r'"\u20ac"', "\u20ac"),
    (r'"\ud55c"', "\ud55c"),
    (r'"\ud800\udf48"', "\U00010348"),
    (r'"\udbe5\udeb3"', "\U001096b3"),

    # Multiple characters
    ('"foo"', "foo"),
    (r'"foo\/bar"', "foo/bar"),
])
def test_string(json: ModuleType, s: str, expected: Any) -> None:
    """Test JSON string."""
    assert json.loads(s) == expected


@pytest.mark.parametrize(("s", "msg", "colno", "end_colno"), [
    ('"foo', "Unterminated string", 1, 5),
    ('"foo\n', "Unterminated string", 1, 5),
    ('"\b"', "Unescaped control character", 2, 3),
    ('"\\', "Expecting escaped character", 3, 0),
    ('"\\\n', "Expecting escaped character", 3, 0),
    (r'"\a"', "Invalid backslash escape", 2, 4),
    (r'"\u"', "Expecting 4 hex digits", 4, 8),
    (r'"\u0xff"', "Expecting 4 hex digits", 4, 8),
    (r'"\u????"', "Expecting 4 hex digits", 4, 8),
    (r'"\ud800"', "Surrogates are not allowed", 2, 8),
    (r'"\ud800\u"', "Expecting 4 hex digits", 10, 14),
    (r'"\ud800\u0xff"', "Expecting 4 hex digits", 10, 14),
    (r'"\ud800\u????"', "Expecting 4 hex digits", 10, 14),
    (r'"\ud800\u0024"', "Surrogates are not allowed", 2, 8),
    (r'"\udf48"', "Surrogates are not allowed", 2, 8),
])
def test_invalid_string(
    json: ModuleType, s: str, msg: str, colno: int, end_colno: int,
) -> None:
    """Test invalid JSON string."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s)

    _check_syntax_err(exc_info, msg, colno, end_colno)


@pytest.mark.parametrize(("s", "expected"), [
    (r'"\ud800"', "\ud800"),
    (r'"\ud800\u0024"', "\ud800$"),
    (r'"\udf48"', "\udf48"),
])
def test_surrogates(json: ModuleType, s: str, expected: Any) -> None:
    """Test surrogates."""
    assert json.loads(s, allow=SURROGATES) == expected


@pytest.mark.parametrize(("s", "expected"), [
    # Empty array
    ("[]", []),

    # One value
    ('[""]', [""]),
    ("[0]", [0]),
    ("[0.0]", [0.0]),
    ("[{}]", [{}]),
    ("[[]]", [[]]),
    ("[true]", [True]),
    ("[false]", [False]),
    ("[null]", [None]),

    # Multiple values
    ("[1, 2, 3]", [1, 2, 3]),
])  # type: ignore
def test_array(json: ModuleType, s: str, expected: Any) -> None:
    """Test JSON array."""
    assert json.loads(s) == expected


@pytest.mark.parametrize(("s", "expected"), [
    # In empty array
    ("[ ]", []),

    # Before first element
    ("[ 1,2,3]", [1, 2, 3]),

    # Before comma's
    ("[1 ,2 ,3]", [1, 2, 3]),

    # After comma's
    ("[1, 2, 3]", [1, 2, 3]),

    # After last element
    ("[1,2,3 ]", [1, 2, 3]),
])
def test_array_whitespace(json: ModuleType, s: str, expected: Any) -> None:
    """Test whitespace in JSON array."""
    assert json.loads(s) == expected


@pytest.mark.parametrize(("s", "expected"), [
    # In empty array
    ("[/**/]", []),

    # Before first element
    ("[/**/1,2,3]", [1, 2, 3]),

    # Before comma's
    ("[1/**/,2/**/,3]", [1, 2, 3]),

    # After comma's
    ("[1,/**/2,/**/3]", [1, 2, 3]),

    # After last element
    ("[1,2,3/**/]", [1, 2, 3]),
])
def test_array_comments(json: ModuleType, s: str, expected: Any) -> None:
    """Test comments in JSON array."""
    assert json.loads(s, allow=COMMENTS) == expected


@pytest.mark.parametrize(("s", "msg", "colno", "end_colno"), [
    ("[", "Unterminated array", 1, 2),
    ("[0", "Unterminated array", 1, 3),
    ("[1-2-3]", "Expecting comma", 3, 0),
    ("[1 2 3]", "Missing comma's are not allowed", 3, 0),
    ("[0,", "Unterminated array", 1, 4),
    ("[0,]", "Trailing comma is not allowed", 3, 4),
])
def test_invalid_array(
    json: ModuleType, s: str, msg: str, colno: int, end_colno: int,
) -> None:
    """Test invalid JSON array."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s)

    _check_syntax_err(exc_info, msg, colno, end_colno)


@pytest.mark.parametrize(("s", "expected"), [
    # Empty object
    ("{}", {}),

    # One value
    ('{"a": ""}', {"a": ""}),
    ('{"a": 0}', {"a": 0}),
    ('{"a": 0.0}', {"a": 0.0}),
    ('{"a": {}}', {"a": {}}),
    ('{"a": []}', {"a": []}),
    ('{"a": true}', {"a": True}),
    ('{"a": false}', {"a": False}),
    ('{"a": null}', {"a": None}),

    # Multiple values
    ('{"a": 0, "b": 0, "c": 0}', {"a": 0, "b": 0, "c": 0}),
])  # type: ignore
def test_object(json: ModuleType, s: str, expected: Any) -> None:
    """Test JSON object."""
    assert json.loads(s) == expected


@pytest.mark.parametrize(("s", "expected"), [
    # In empty object
    ("{ }", {}),

    # Before first element
    ('{ "a":0,"b":0,"c":0}', {"a": 0, "b": 0, "c": 0}),

    # Before colon
    ('{"a" :0,"b" :0,"c" :0}', {"a": 0, "b": 0, "c": 0}),

    # After colon
    ('{"a": 0,"b": 0,"c": 0}', {"a": 0, "b": 0, "c": 0}),

    # Before comma
    ('{"a":0 ,"b":0 ,"c":0}', {"a": 0, "b": 0, "c": 0}),

    # After comma
    ('{"a":0, "b":0, "c":0}', {"a": 0, "b": 0, "c": 0}),

    # After last element
    ('{"a":0,"b":0,"c":0 }', {"a": 0, "b": 0, "c": 0}),
])
def test_object_whitespace(json: ModuleType, s: str, expected: Any) -> None:
    """Test whitespace in JSON object."""
    assert json.loads(s) == expected


@pytest.mark.parametrize(("s", "expected"), [
    # In empty object
    ("{/**/}", {}),

    # Before first element
    ('{/**/"a":0,"b":0,"c":0}', {"a": 0, "b": 0, "c": 0}),

    # Before colon
    ('{"a"/**/:0,"b"/**/:0,"c"/**/:0}', {"a": 0, "b": 0, "c": 0}),

    # After colon
    ('{"a":/**/0,"b":/**/0,"c":/**/0}', {"a": 0, "b": 0, "c": 0}),

    # Before comma
    ('{"a":0/**/,"b":0/**/,"c":0}', {"a": 0, "b": 0, "c": 0}),

    # After comma
    ('{"a":0,/**/"b":0,/**/"c":0}', {"a": 0, "b": 0, "c": 0}),

    # After last element
    ('{"a":0,"b":0,"c":0/**/}', {"a": 0, "b": 0, "c": 0}),
])
def test_object_comments(json: ModuleType, s: str, expected: Any) -> None:
    """Test comments in JSON object."""
    assert json.loads(s, allow=COMMENTS) == expected


@pytest.mark.parametrize(("s", "msg", "colno", "end_colno"), [
    ("{", "Unterminated object", 1, 2),
    ("{0: 0}", "Expecting string", 2, 0),
    ('{"a": 1, "a": 2, "a": 3}', "Duplicate keys are not allowed", 10, 13),
    ('{"a"}', "Expecting colon", 5, 0),
    ('{"a": 0', "Unterminated object", 1, 8),
    ('{"a": 0"b": 0"c": 0}', "Expecting comma", 8, 0),
    ('{"a": 0 "b": 0 "c": 0}', "Missing comma's are not allowed", 8, 0),
    ('{"a": 1, 2, 3}', "Expecting string", 10, 0),
    ('{"a": 0,', "Unterminated object", 1, 9),
    ('{"a": 0,}', "Trailing comma is not allowed", 8, 9),
])
def test_invalid_object(
    json: ModuleType, s: str, msg: str, colno: int, end_colno: int,
) -> None:
    """Test invalid JSON object."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s)

    _check_syntax_err(exc_info, msg, colno, end_colno)


def test_duplicate_keys(json: ModuleType) -> None:
    """Test duplicate keys."""
    obj: dict[str, int] = json.loads(
        '{"a": 1, "a": 2, "a": 3}', allow=DUPLICATE_KEYS,
    )
    assert list(map(str, obj.keys())) == ["a", "a", "a"]
    assert list(obj.values()) == [1, 2, 3]


def test_reuse_keys(json: ModuleType) -> None:
    """Test if keys are re-used."""
    obj: list[dict[str, int]] = json.loads('[{"a": 1}, {"a": 2}, {"a": 3}]')
    ids: set[int] = {id(next(iter(value.keys()))) for value in obj}
    assert len(ids) == 1


@pytest.mark.parametrize(("s", "expected"), [
    ("[1 2 3]", [1, 2, 3]),
    ('{"a": 0 "b": 0 "c": 0}', {"a": 0, "b": 0, "c": 0}),
])
def test_missing_commas(json: ModuleType, s: str, expected: Any) -> None:
    """Test missing comma's."""
    assert json.loads(s, allow=MISSING_COMMAS) == expected


@pytest.mark.parametrize(("s", "expected"), [
    ("[0,]", [0]),
    ('{"a": 0,}', {"a": 0}),
])
def test_trailing_comma(json: ModuleType, s: str, expected: Any) -> None:
    """Test trailing comma."""
    assert json.loads(s, allow=TRAILING_COMMA) == expected


@pytest.mark.parametrize("s", [
    # Before value
    " 0",

    # After value
    "0 ",
])
def test_value_whitespace(json: ModuleType, s: str) -> None:
    """Test whitespace around JSON value."""
    assert json.loads(s) == 0


@pytest.mark.parametrize("s", [
    # Before value
    "/**/0",

    # After value
    "0/**/",
])
def test_value_comments(json: ModuleType, s: str) -> None:
    """Test comments around JSON value."""
    assert json.loads(s, allow=COMMENTS) == 0


@pytest.mark.parametrize("s", ["", "-", "foo"])
def test_invalid_value(json: ModuleType, s: str) -> None:
    """Test invalid JSON value."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s)

    _check_syntax_err(exc_info, "Expecting value", 1)


@pytest.mark.parametrize("s", [
    # One character
    "0 ",
    "0\t",
    "0\n",
    "0\r",

    # Multiple characters
    "0   ",
])
def test_whitespace(json: ModuleType, s: str) -> None:
    """Test whitespace."""
    assert json.loads(s) == 0


@pytest.mark.parametrize("s", [
    # One comment
    "0//line comment",
    "0/*block comment*/",

    # Multiple comments
    "0//comment 1\n//comment 2\n//comment 3",
    "0/*comment 1*//*comment 2*//*comment 3*/",

    # Whitespace
    "0 //comment 1\n //comment 2\n //comment 3\n ",
    "0 /*comment 1*/ /*comment 2*/ /*comment 3*/ ",
])
def test_comments(json: ModuleType, s: str) -> None:
    """Test comments."""
    assert json.loads(s, allow=COMMENTS) == 0


def test_invalid_comment(json: ModuleType) -> None:
    """Test invalid comment."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads("0/*unterminated comment", allow=COMMENTS)

    _check_syntax_err(exc_info, "Unterminated comment", 2, 24)


@pytest.mark.parametrize("s", [
    "0//line comment",
    "0/*block comment*/",
    "0/*unterminated comment",
])
def test_comments_not_allowed(json: ModuleType, s: str) -> None:
    """Test comments if not allowed."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads(s)

    _check_syntax_err(exc_info, "Comments are not allowed", 2, len(s) + 1)


def test_end_of_file(json: ModuleType) -> None:
    """Test end of file."""
    with pytest.raises(json.JSONSyntaxError) as exc_info:
        json.loads("1 2 3")

    _check_syntax_err(exc_info, "Expecting end of file", 3)
