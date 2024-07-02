"""JSON decoder."""
# Copyright (C) 2024 Nice Zombies
from __future__ import annotations

__all__: list[str] = ["JSONDecodeError", "JSONDecoder"]

import re
from re import DOTALL, MULTILINE, VERBOSE, Match, Pattern, RegexFlag
from typing import Any, Callable

from jsonc.scanner import make_scanner

FLAGS: RegexFlag = VERBOSE | MULTILINE | DOTALL


class JSONDecodeError(ValueError):
    """JSON decode error."""

    def __init__(self, msg: str, doc: str, pos: int) -> None:
        """Create new JSON decode error."""
        lineno: int = doc.count("\n", 0, pos) + 1
        colno: int = pos - doc.rfind("\n", 0, pos)
        errmsg: str = f"{msg}: line {lineno} column {colno} (char {pos:d})"
        super().__init__(errmsg)


STRINGCHUNK: Pattern[str] = re.compile(
    r'([^"\\\x00-\x1f]*)(["\\\x00-\x1f])', FLAGS,
)
BACKSLASH: dict[str, str] = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


def _decode_unicode_escape(s: str, pos: int) -> int:
    esc: str = s[pos + 1:pos + 5]
    if len(esc) == 4 and esc[1] not in "xX":
        try:
            return int(esc, 16)
        except ValueError:
            pass

    msg: str = r"Invalid \uXXXX escape"
    raise JSONDecodeError(msg, s, pos)


# Use speedup if available
try:
    from jsonc._accelerator import parse_string
except ImportError:
    # pylint: disable=too-many-locals
    def parse_string(s: str, end: int, /) -> tuple[str, int]:  # noqa: C901
        """Parse JSON string."""
        backslash: dict[str, str] = BACKSLASH
        match_str: Callable[[str, int], Match[str] | None] = STRINGCHUNK.match
        chunks: list[str] = []
        append_chunk: Callable[[str], None] = chunks.append
        begin: int = end - 1
        while True:
            chunk: Match[str] | None = match_str(s, end)
            msg: str
            if not chunk:
                msg = "Unterminated string starting at"
                raise JSONDecodeError(msg, s, begin)

            end = chunk.end()
            content, terminator = chunk.groups()
            # Content is contains zero or more unescaped string characters
            if content:
                append_chunk(content)

            # Terminator is the end of string, a literal control character,
            # or a backslash denoting that an escape sequence follows
            if terminator == '"':
                break

            if terminator != "\\":
                msg = f"Invalid control character {terminator!r} at"
                raise JSONDecodeError(msg, s, end)

            try:
                esc = s[end]
            except IndexError:
                msg = "Unterminated string starting at"
                raise JSONDecodeError(msg, s, begin) from None

            # If not a unicode escape sequence, must be in the lookup table
            if esc != "u":
                try:
                    char = backslash[esc]
                except KeyError:
                    msg = rf"Invalid \escape: {esc!r}"
                    raise JSONDecodeError(msg, s, end) from None

                end += 1
            else:
                uni: int = _decode_unicode_escape(s, end)
                end += 5
                if 0xd800 <= uni <= 0xdbff and s[end:end + 2] == r"\u":
                    uni2: int = _decode_unicode_escape(s, end + 1)
                    if 0xdc00 <= uni2 <= 0xdfff:
                        uni = ((uni - 0xd800) << 10) | (uni2 - 0xdc00)
                        uni += 0x10000
                        end += 6

                char = chr(uni)

            append_chunk(char)

        return "".join(chunks), end


WHITESPACE: Pattern[str] = re.compile(r"[ \t\n\r]*", FLAGS)
WHITESPACE_STR: str = " \t\n\r"


# pylint: disable=too-many-arguments, too-many-locals, too-many-branches,
# pylint: disable=too-many-statements
def parse_object(  # noqa: C901, PLR0912, PLR0915
    s: str, end: int, scan_once: Callable[[str, int], tuple[Any, int]],
    memo: dict[str, str],
) -> tuple[dict[str, Any], int]:
    """Parse JSON object."""
    match_whitespace: Callable[
        [str, int], Match[str],
    ] = WHITESPACE.match  # type: ignore
    whitespace_str: str = WHITESPACE_STR
    pairs: list[tuple[str, Any]] = []
    append_pair: Callable[[tuple[str, Any]], None] = pairs.append
    memo_get: Callable[[str, str], str] = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar: str = s[end:end + 1]
    # Normally we expect nextchar == '"'
    msg: str
    if nextchar != '"':
        if nextchar in whitespace_str:
            end = match_whitespace(s, end).end()
            nextchar = s[end:end + 1]

        # Trivial empty object
        if nextchar == "}":
            return {}, end + 1

        if nextchar != '"':
            msg = "Expecting property name enclosed in double quotes"
            raise JSONDecodeError(msg, s, end)

    end += 1
    while True:
        key, end = parse_string(s, end)
        key = memo_get(key, key)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end:end + 1] != ":":
            end = match_whitespace(s, end).end()
            if s[end:end + 1] != ":":
                msg = "Expecting ':' delimiter"
                raise JSONDecodeError(msg, s, end)

        end += 1
        try:
            if s[end] in whitespace_str:
                end += 1
                if s[end] in whitespace_str:
                    end = match_whitespace(s, end + 1).end()
        except IndexError:
            pass

        try:
            value, end = scan_once(s, end)
        except StopIteration as err:
            msg = "Expecting value"
            raise JSONDecodeError(msg, s, err.value) from None

        append_pair((key, value))
        try:
            nextchar = s[end]
            if nextchar in whitespace_str:
                end = match_whitespace(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ""

        end += 1
        if nextchar == "}":
            break

        if nextchar != ",":
            msg = "Expecting ',' delimiter"
            raise JSONDecodeError(msg, s, end - 1)

        comma_idx: int = end - 1
        end = match_whitespace(s, end).end()
        nextchar = s[end:end + 1]
        end += 1
        if nextchar != '"':
            if nextchar != "}":
                msg = "Expecting property name enclosed in double quotes"
                raise JSONDecodeError(msg, s, end - 1)

            msg = "Illegal trailing comma before end of object"
            raise JSONDecodeError(msg, s, comma_idx)

    return dict(pairs), end


def parse_array(  # noqa: C901
    s: str, end: int, scan_once: Callable[[str, int], tuple[Any, int]],
) -> tuple[list[Any], int]:
    """Parse JSON array."""
    match_whitespace: Callable[
        [str, int], Match[str],
    ] = WHITESPACE.match  # type: ignore
    whitespace_str: str = WHITESPACE_STR
    values: list[Any] = []
    nextchar: str = s[end:end + 1]
    if nextchar in whitespace_str:
        end = match_whitespace(s, end + 1).end()
        nextchar = s[end:end + 1]

    # Look-ahead for trivial empty array
    if nextchar == "]":
        return values, end + 1

    append_value: Callable[[Any], None] = values.append
    while True:
        msg: str
        try:
            value, end = scan_once(s, end)
        except StopIteration as err:
            msg = "Expecting value"
            raise JSONDecodeError(msg, s, err.value) from None

        append_value(value)
        nextchar = s[end:end + 1]
        if nextchar in whitespace_str:
            end = match_whitespace(s, end + 1).end()
            nextchar = s[end:end + 1]

        end += 1
        if nextchar == "]":
            break

        if nextchar != ",":
            msg = "Expecting ',' delimiter"
            raise JSONDecodeError(msg, s, end - 1)

        comma_idx: int = end - 1
        try:
            if s[end] in whitespace_str:
                end += 1
                if s[end] in whitespace_str:
                    end = match_whitespace(s, end + 1).end()

            nextchar = s[end:end + 1]
        except IndexError:
            pass

        if nextchar == "]":
            msg = "Illegal trailing comma before end of array"
            raise JSONDecodeError(msg, s, comma_idx)

    return values, end


# pylint: disable=too-few-public-methods
class JSONDecoder:
    """JSON decoder."""

    def __init__(self) -> None:
        """Create new JSON decoder."""
        self.parse_object: Callable[[
            str, int, Callable[[str, int], tuple[Any, int]], dict[str, str],
        ], tuple[dict[str, Any], int]] = parse_object
        self.parse_array: Callable[
            [str, int, Any], tuple[list[Any], int],
        ] = parse_array
        self.parse_string: Callable[[str, int], tuple[str, int]] = parse_string
        self.memo: dict[str, str] = {}
        self.scan_once: Callable[
            [str, int], tuple[Any, int],
        ] = make_scanner(self)  # type: ignore

    def decode(self, s: str) -> Any:
        """Decode a JSON document."""
        match_whitespace: Callable[
            [str, int], Match[str],
        ] = WHITESPACE.match  # type: ignore
        idx: int = match_whitespace(s, 0).end()
        msg: str
        try:
            obj, end = self.scan_once(s, idx)
        except StopIteration as err:
            msg = "Expecting value"
            raise JSONDecodeError(msg, s, err.value) from None

        end = match_whitespace(s, end).end()
        if end < len(s):
            msg = "Extra data"
            raise JSONDecodeError(msg, s, end)

        return obj
