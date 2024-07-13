# Copyright (C) 2024 Nice Zombies
"""JSON scanner."""
from __future__ import annotations

__all__ = ["JSONSyntaxError", "format_error", "make_scanner"]

import re
from math import inf, nan
from re import DOTALL, MULTILINE, VERBOSE, Match
from shutil import get_terminal_size
from typing import TYPE_CHECKING

from typing_extensions import Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from jsonyx.decoder import JSONDecoder

_match_number: Callable[[str, int], Match[str] | None] = re.compile(
    r"(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?", VERBOSE | MULTILINE | DOTALL,
).match


def _get_err_context(doc: str, pos: int) -> tuple[int, str]:
    line_start: int = doc.rfind("\n", 0, pos) + 1
    if (line_end := doc.find("\n", pos)) == -1:
        line_end = len(doc)

    max_chars: int = get_terminal_size().columns - 4  # leading spaces
    min_start: int = min(line_end - max_chars, pos - max_chars // 2)
    max_end: int = max(line_start + max_chars, pos + max_chars // 2)
    text_start: int = max(min_start, line_start)
    text_end: int = min(line_end, max_end)
    text: str = doc[text_start:text_end].expandtabs(1)
    if text_start > line_start:
        text = "..." + text[3:]

    if text_end < line_end:
        text = text[:-3] + "..."

    offset: int = pos - text_start + 1
    return offset, text


def format_error(exc: JSONSyntaxError) -> str:
    """Format JSON syntax error."""
    caret_line: str = " " * (exc.offset - 1) + "^"  # type: ignore
    exc_type: type[JSONSyntaxError] = type(exc)
    return f"""\
  File {exc.filename!r}, line {exc.lineno:d}, column {exc.colno:d}
    {exc.text}
    {caret_line}
{exc_type.__module__}.{exc_type.__qualname__}: {exc.msg}\
"""


class JSONSyntaxError(SyntaxError):
    """JSON syntax error."""

    def __init__(self, msg: str, filename: str, doc: str, pos: int) -> None:
        """Create new JSON syntax error."""
        lineno: int = doc.count("\n", 0, pos) + 1
        self.colno: int = pos - doc.rfind("\n", 0, pos)
        offset, text = _get_err_context(doc, pos)
        super().__init__(msg, (filename, lineno, offset, text))

    def __str__(self) -> str:
        """Convert to string."""
        return (
            f"{self.msg} (file {self.filename}, line {self.lineno:d}, column "
            f"{self.colno: d})"
        )


try:
    from jsonyx._accelerator import make_scanner
except ImportError:
    # pylint: disable-next=R0915
    def make_scanner(context: JSONDecoder) -> (   # noqa: C901, PLR0915
        Callable[[str, str, int], tuple[Any, int]]
    ):
        """Make JSON scanner."""
        allow_nan: bool = context.allow_nan
        memo: dict[str, str] = {}
        memoize: Callable[[str, str], str] = memo.setdefault
        parse_array: Callable[[
            JSONDecoder, str, str, int,
            Callable[[str, str, int], tuple[Any, int]],
        ], tuple[list[Any], int]] = context.parse_array
        parse_object: Callable[[
            JSONDecoder, str, str, int,
            Callable[[str, str, int], tuple[Any, int]],
            Callable[[str, str], str],
        ], tuple[dict[str, Any], int]] = context.parse_object
        parse_string: Callable[
            [str, str, int], tuple[str, int],
        ] = context.parse_string

        # pylint: disable-next=R0912
        def _scan_once(  # noqa: C901, PLR0912
            filename: str, s: str, idx: int,
        ) -> tuple[Any, int]:
            try:
                nextchar = s[idx]
            except IndexError:
                msg: str = "Expecting value"
                raise JSONSyntaxError(msg, filename, s, idx) from None

            result: Any
            if nextchar == '"':
                result, end = parse_string(filename, s, idx + 1)
            elif nextchar == "{":
                result, end = parse_object(
                    context, filename, s, idx + 1, _scan_once, memoize,
                )
            elif nextchar == "[":
                result, end = parse_array(
                    context, filename, s, idx + 1, _scan_once,
                )
            elif nextchar == "n" and s[idx:idx + 4] == "null":
                result, end = None, idx + 4
            elif nextchar == "t" and s[idx:idx + 4] == "true":
                result, end = True, idx + 4
            elif nextchar == "f" and s[idx:idx + 5] == "false":
                result, end = False, idx + 5
            elif number := _match_number(s, idx):
                integer, frac, exp = number.groups()
                end = number.end()
                if frac or exp:
                    result = float(integer + (frac or "") + (exp or ""))
                else:
                    result = int(integer)
            elif nextchar == "N" and s[idx:idx + 3] == "NaN":
                if not allow_nan:
                    msg: str = "NaN isn't allowed"
                    raise JSONSyntaxError(msg, filename, s, idx)

                result, end = nan, idx + 3
            elif nextchar == "I" and s[idx:idx + 8] == "Infinity":
                if not allow_nan:
                    msg = "Infinity isn't allowed"
                    raise JSONSyntaxError(msg, filename, s, idx)

                result, end = inf, idx + 8
            elif nextchar == "-" and s[idx:idx + 9] == "-Infinity":
                if not allow_nan:
                    msg = "Infinity isn't allowed"
                    raise JSONSyntaxError(msg, filename, s, idx)

                result, end = -inf, idx + 9
            else:
                msg = "Expecting value"
                raise JSONSyntaxError(msg, filename, s, idx)

            return result, end

        def scan_once(filename: str, s: str, idx: int) -> tuple[Any, int]:
            try:
                return _scan_once(filename, s, idx)
            finally:
                memo.clear()

        return scan_once
