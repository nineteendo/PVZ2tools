# Copyright (C) 2024 Nice Zombies
"""JSON decoder."""
from __future__ import annotations

__all__: list[str] = ["DuplicateKey", "JSONDecoder"]

import re
from re import DOTALL, MULTILINE, VERBOSE, Match, RegexFlag
from typing import TYPE_CHECKING

from typing_extensions import Any, Literal

from jsonyx.scanner import JSONSyntaxError, make_scanner

if TYPE_CHECKING:
    from collections.abc import Callable, Container

FLAGS: RegexFlag = VERBOSE | MULTILINE | DOTALL
UNESCAPE: dict[str, str] = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}

_match_chunk: Callable[[str, int], Match[str] | None] = re.compile(
    r'[^"\\\x00-\x1f]+', FLAGS,
).match


def _unescape_unicode(filename: str, s: str, pos: int) -> int:
    esc: str = s[pos:pos + 4]
    if len(esc) == 4 and esc[1] not in "xX":
        try:
            return int(esc, 16)
        except ValueError:
            pass

    msg: str = "Expecting 4 hex digits"
    raise JSONSyntaxError(msg, filename, s, pos)


try:
    # pylint: disable-next=C0412
    from jsonyx._accelerator import scanstring
except ImportError:
    def scanstring(filename: str, s: str, end: int, /) -> (  # noqa: C901
        tuple[str, int]
    ):
        """Scan JSON string."""
        chunks: list[str] = []
        append_chunk: Callable[[str], None] = chunks.append
        str_idx: int = end - 1
        while True:
            # Match one or more unescaped string characters
            if match := _match_chunk(s, end):
                end = match.end()
                append_chunk(match.group())

            # Terminator is the end of string, a literal control character,
            # or a backslash denoting that an escape sequence follows
            try:
                terminator: str = s[end]
            except IndexError:
                msg: str = "Unterminated string"
                raise JSONSyntaxError(msg, filename, s, str_idx) from None

            if terminator == '"':
                return "".join(chunks), end + 1

            if terminator != "\\":
                if terminator == "\n":
                    msg = "Unterminated string"
                    raise JSONSyntaxError(msg, filename, s, str_idx)

                msg = "Unescaped control character"
                raise JSONSyntaxError(msg, filename, s, end)

            end += 1
            try:
                esc = s[end]
            except IndexError:
                msg = "Invalid backslash escape"
                raise JSONSyntaxError(msg, filename, s, end) from None

            # If not a unicode escape sequence, must be in the lookup table
            if esc != "u":
                try:
                    char = UNESCAPE[esc]
                except KeyError:
                    msg = "Invalid backslash escape"
                    raise JSONSyntaxError(msg, filename, s, end) from None

                end += 1
            else:
                uni: int = _unescape_unicode(filename, s, end + 1)
                end += 5
                if 0xd800 <= uni <= 0xdbff and s[end:end + 2] == r"\u":
                    uni2: int = _unescape_unicode(filename, s, end + 2)
                    if 0xdc00 <= uni2 <= 0xdfff:
                        uni = ((uni - 0xd800) << 10) | (uni2 - 0xdc00)
                        uni += 0x10000
                        end += 6

                char = chr(uni)

            append_chunk(char)


_match_whitespace: Callable[[str, int], Match[str] | None] = re.compile(
    r"[ \t\n\r]+", FLAGS,
).match


def _skip_comments(context: JSONDecoder, filename: str, s: str, end: int) -> (
    int
):
    while True:
        if match := _match_whitespace(s, end):
            end = match.end()

        if (comment_prefix := s[end:end + 2]) == "//":
            if not context.allow_comments:
                msg: str = "Comments aren't allowed"
                raise JSONSyntaxError(msg, filename, s, end)

            if (end := s.find("\n", end + 2)) == -1:
                return len(s)

            end += 1
        elif comment_prefix == "/*":
            if not context.allow_comments:
                msg = "Comments aren't allowed"
                raise JSONSyntaxError(msg, filename, s, end)

            comment_idx: int = end
            if (end := s.find("*/", end + 2)) == -1:
                msg = "Unterminated comment"
                raise JSONSyntaxError(msg, filename, s, comment_idx)

            end += 2
        else:
            return end


try:
    from jsonyx._accelerator import DuplicateKey  # type: ignore
except ImportError:
    class DuplicateKey(str):
        """Duplicate key."""

        __slots__: tuple[()] = ()

        def __hash__(self) -> int:
            """Return hash."""
            return id(self)


# pylint: disable-next=R0913, R0912
def parse_object(  # noqa: C901, PLR0917, PLR0913, PLR0912
    context: JSONDecoder,
    filename: str,
    s: str,
    end: int,
    scan_once: Callable[[str, str, int], tuple[Any, int]],
    memoize: Callable[[str, str], str],
) -> tuple[dict[str, Any], int]:
    """Parse JSON object."""
    end = _skip_comments(context, filename, s, end)
    if (nextchar := s[end:end + 1]) != '"':
        if nextchar != "}":
            msg: str = "Expecting string"
            raise JSONSyntaxError(msg, filename, s, end)

        return {}, end + 1

    result: dict[str, Any] = {}
    while True:
        key_idx: int = end
        key, end = scanstring(filename, s, end + 1)

        if key not in result:
            # Reduce memory consumption
            key = memoize(key, key)
        elif not context.allow_duplicate_keys:
            msg = "Duplicate keys aren't allowed"
            raise JSONSyntaxError(msg, filename, s, key_idx)
        else:
            key = DuplicateKey(key)

        if s[end:end + 1] != ":":
            colon_idx: int = end
            end = _skip_comments(context, filename, s, end)
            if s[end:end + 1] != ":":
                msg = "Expecting ':' delimiter"
                raise JSONSyntaxError(msg, filename, s, colon_idx)

        end = _skip_comments(context, filename, s, end + 1)
        result[key], end = scan_once(filename, s, end)
        if s[end:end + 1] != ",":
            comma_idx: int = end
            end = _skip_comments(context, filename, s, end)
            if (nextchar := s[end:end + 1]) != ",":
                if nextchar != "}":
                    msg = "Expecting ',' delimiter"
                    raise JSONSyntaxError(msg, filename, s, comma_idx)

                return result, end + 1

        comma_idx = end
        end = _skip_comments(context, filename, s, end + 1)
        if (nextchar := s[end:end + 1]) != '"':
            if nextchar != "}":
                msg = "Expecting string"
                raise JSONSyntaxError(msg, filename, s, end)

            if not context.allow_trailing_comma:
                msg = "Trailing comma's aren't allowed"
                raise JSONSyntaxError(msg, filename, s, comma_idx)

            return result, end + 1


def parse_array(
    context: JSONDecoder,
    filename: str,
    s: str,
    end: int,
    scan_once: Callable[[str, str, int], tuple[Any, int]],
) -> tuple[list[Any], int]:
    """Parse JSON array."""
    end = _skip_comments(context, filename, s, end)
    if (nextchar := s[end:end + 1]) == "]":
        return [], end + 1

    values: list[Any] = []
    append_value: Callable[[Any], None] = values.append
    while True:
        value, end = scan_once(filename, s, end)
        append_value(value)
        if s[end:end + 1] != ",":
            comma_idx: int = end
            end = _skip_comments(context, filename, s, end)
            if (nextchar := s[end:end + 1]) != ",":
                if nextchar == "]":
                    return values, end + 1

                msg: str = "Expecting ',' delimiter"
                raise JSONSyntaxError(msg, filename, s, comma_idx)

        comma_idx = end
        end = _skip_comments(context, filename, s, end + 1)
        if s[end:end + 1] == "]":
            if context.allow_trailing_comma:
                return values, end + 1

            msg = "Trailing comma's aren't allowed"
            raise JSONSyntaxError(msg, filename, s, comma_idx)


class JSONDecoder:  # pylint: disable=R0903, R0902
    """JSON decoder."""

    def __init__(
        self,
        *,
        allow: Container[Literal[
            "comments", "duplicate_keys", "nan", "trailing_comma",
        ] | str] = (),
    ) -> None:
        """Create new JSON decoder."""
        self.allow_comments: bool = "comments" in allow
        self.allow_duplicate_keys: bool = "duplicate_keys" in allow
        self.allow_nan: bool = "nan" in allow
        self.allow_trailing_comma: bool = "trailing_comma" in allow
        self.parse_array: Callable[[
            JSONDecoder, str, str, int,
            Callable[[str, str, int], tuple[Any, int]],
        ], tuple[list[Any], int]] = parse_array
        self.parse_object: Callable[[
            JSONDecoder, str, str, int,
            Callable[[str, str, int], tuple[Any, int]],
            Callable[[str, str], str],
        ], tuple[dict[str, Any], int]] = parse_object
        self.parse_string: Callable[
            [str, str, int], tuple[str, int],
        ] = scanstring
        self.scan_once: Callable[
            [str, str, int], tuple[Any, int],
        ] = make_scanner(self)  # type: ignore

    def decode(self, s: str, *, filename: str = "<string>") -> Any:
        """Decode a JSON document."""
        end: int = _skip_comments(self, filename, s, 0)
        try:
            obj, end = self.scan_once(filename, s, end)
        except JSONSyntaxError as exc:
            raise exc.with_traceback(None) from None

        if (end := _skip_comments(self, filename, s, end)) < len(s):
            msg: str = "Extra data"
            raise JSONSyntaxError(msg, filename, s, end)

        return obj
