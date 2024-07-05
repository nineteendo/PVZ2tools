# Copyright (C) 2024 Nice Zombies
"""JSON scanner."""
from __future__ import annotations

__all__ = ["make_scanner"]

import re
from math import inf, nan
from re import DOTALL, MULTILINE, VERBOSE, Match, Pattern
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from jsonc.decoder import JSONDecoder

NUMBER: Pattern[str] = re.compile(
    r"(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?", VERBOSE | MULTILINE | DOTALL,
)


try:
    from jsonc._accelerator import make_scanner
except ImportError:
    def make_scanner(decoder: JSONDecoder) -> (   # noqa: C901
        Callable[[str, str, int], tuple[Any, int]]
    ):
        """Make JSON scanner."""
        parse_object: Callable[[
            str, str, int, Callable[[str, str, int], tuple[Any, int]],
            dict[str, str],
        ], tuple[dict[str, Any], int]] = decoder.parse_object
        parse_array: Callable[[
            str, str, int, Callable[[str, str, int], tuple[Any, int]],
        ], tuple[list[Any], int]] = decoder.parse_array
        parse_string: Callable[
            [str, str, int], tuple[str, int],
        ] = decoder.parse_string
        match_number: Callable[[str, int], Match[str] | None] = NUMBER.match
        memo: dict[str, str] = {}

        # pylint: disable-next=R0912
        def _scan_once(  # noqa: C901, PLR0912
            filename: str, string: str, idx: int,
        ) -> tuple[Any, int]:
            try:
                nextchar = string[idx]
            except IndexError:
                raise StopIteration(idx) from None

            result: Any
            if nextchar == '"':
                result, end = parse_string(filename, string, idx + 1)
            elif nextchar == "{":
                result, end = parse_object(
                    filename, string, idx + 1, _scan_once, memo,
                )
            elif nextchar == "[":
                result, end = parse_array(
                    filename, string, idx + 1, _scan_once,
                )
            elif nextchar == "n" and string[idx:idx + 4] == "null":
                result, end = None, idx + 4
            elif nextchar == "t" and string[idx:idx + 4] == "true":
                result, end = True, idx + 4
            elif nextchar == "f" and string[idx:idx + 5] == "false":
                result, end = False, idx + 5
            elif number := match_number(string, idx):
                integer, frac, exp = number.groups()
                end = number.end()
                if frac or exp:
                    result = float(integer + (frac or "") + (exp or ""))
                else:
                    result = int(integer)
            elif nextchar == "N" and string[idx:idx + 3] == "NaN":
                result, end = nan, idx + 3
            elif nextchar == "I" and string[idx:idx + 8] == "Infinity":
                result, end = inf, idx + 8
            elif nextchar == "-" and string[idx:idx + 9] == "-Infinity":
                result, end = -inf, idx + 9
            else:
                raise StopIteration(idx)

            return result, end

        def scan_once(filename: str, string: str, idx: int) -> tuple[Any, int]:
            try:
                return _scan_once(filename, string, idx)
            finally:
                memo.clear()

        return scan_once
