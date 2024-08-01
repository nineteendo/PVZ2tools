# Copyright (C) 2024 Nice Zombies
"""JSON encoder."""
from __future__ import annotations

__all__: list[str] = ["make_encoder"]

import re
from decimal import Decimal
from io import StringIO
from math import inf, isfinite
from re import Match
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, ItemsView

_ESCAPE_DCT: dict[str, str] = {chr(i): f"\\u{i:04x}" for i in range(0x20)} | {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}

_escape: Callable[[Callable[[Match[str]], str], str], str] = re.compile(
    r'["\\\x00-\x1f]',
).sub
_escape_ascii: Callable[[Callable[[Match[str]], str], str], str] = re.compile(
    r'(?:["\\]|[^\x20-\x7e])',
).sub

try:
    if not TYPE_CHECKING:
        from _jsonyx import make_encoder
except ImportError:
    # pylint: disable-next=R0915, R0913, R0914
    def make_encoder(  # noqa: C901, PLR0915, PLR0917, PLR0913
        encode_decimal: Callable[[Decimal], str],
        indent: str | None,
        end: str,
        item_separator: str,
        key_separator: str,
        allow_nan_and_infinity: bool,  # noqa: FBT001
        allow_surrogates: bool,  # noqa: FBT001
        ensure_ascii: bool,  # noqa: FBT001
        sort_keys: bool,  # noqa: FBT001
        trailing_comma: bool,  # noqa: FBT001
    ) -> Callable[[object], str]:
        """Make JSON encoder."""
        float_repr: Callable[[float], str] = float.__repr__
        int_repr: Callable[[int], str] = int.__repr__
        markers: dict[int, object] = {}

        if not ensure_ascii:
            def replace(match: Match[str]) -> str:
                return _ESCAPE_DCT[match.group()]

            def encode_string(s: str) -> str:
                return f'"{_escape(replace, s)}"'
        else:
            def replace(match: Match[str]) -> str:
                s: str = match.group()
                try:
                    return _ESCAPE_DCT[s]
                except KeyError:
                    if (uni := ord(s)) >= 0x10000:
                        # surrogate pair
                        uni -= 0x10000
                        uni1: int = 0xd800 | ((uni >> 10) & 0x3ff)
                        uni2: int = 0xdc00 | (uni & 0x3ff)
                        return f"\\u{uni1:04x}\\u{uni2:04x}"

                    if 0xd800 <= uni <= 0xdfff and not allow_surrogates:
                        msg: str = "Surrogates are not allowed"
                        raise ValueError(msg) from None

                    return f"\\u{uni:04x}"

            def encode_string(s: str) -> str:
                return f'"{_escape_ascii(replace, s)}"'

        def floatstr(num: float) -> str:
            if isfinite(num):
                return float_repr(num)

            if not allow_nan_and_infinity:
                msg: str = f"{num!r} is not allowed"
                raise ValueError(msg)

            if num == inf:
                return "Infinity"

            if num == -inf:
                return "-Infinity"

            return "NaN"

        def write_list(
            lst: list[object], write: Callable[[str], object], old_indent: str,
        ) -> None:
            if not lst:
                write("[]")
                return

            if (markerid := id(lst)) in markers:
                msg: str = "Unexpected circular reference"
                raise ValueError(msg)

            markers[markerid] = lst
            write("[")
            current_indent: str = old_indent
            current_item_separator: str = item_separator
            if indent is not None:
                current_indent += indent
                current_item_separator += current_indent
                write(current_indent)

            first: bool = True
            for value in lst:
                if first:
                    first = False
                else:
                    write(current_item_separator)

                write_value(value, write, current_indent)

            del markers[markerid]
            if indent is not None:
                if trailing_comma:
                    write(item_separator)

                write(old_indent)

            write("]")

        def write_dict(
            dct: dict[object, object], write: Callable[[str], object],
            old_indent: str,
        ) -> None:
            if not dct:
                write("{}")
                return

            if (markerid := id(dct)) in markers:
                msg: str = "Unexpected circular reference"
                raise ValueError(msg)

            markers[markerid] = dct
            write("{")
            current_indent: str = old_indent
            current_item_separator: str = item_separator
            if indent is not None:
                current_indent += indent
                current_item_separator += current_indent
                write(current_indent)

            first: bool = True
            items: ItemsView[object, object] = dct.items()
            for key, value in sorted(items) if sort_keys else items:
                if not isinstance(key, str):
                    msg = f"Keys must be str, not {type(key).__name__}"
                    raise TypeError(msg)

                if first:
                    first = False
                else:
                    write(current_item_separator)

                write(encode_string(key) + key_separator)
                write_value(value, write, current_indent)

            del markers[markerid]
            if indent is not None:
                if trailing_comma:
                    write(item_separator)

                write(old_indent)

            write("}")

        def write_value(
            obj: object, write: Callable[[str], object], current_indent: str,
        ) -> None:
            if isinstance(obj, str):
                write(encode_string(obj))
            elif obj is None:
                write("null")
            elif isinstance(obj, int):
                if obj is True:
                    write("true")
                elif obj is False:
                    write("false")
                else:
                    write(int_repr(obj))
            elif isinstance(obj, float):
                write(floatstr(obj))
            elif isinstance(obj, list):
                write_list(obj, write, current_indent)  # type: ignore
            elif isinstance(obj, dict):
                write_dict(obj, write, current_indent)  # type: ignore
            elif isinstance(obj, Decimal):
                write(encode_decimal(obj))
            else:
                msg: str = f"{type(obj).__name__} is not JSON serializable"
                raise TypeError(msg)

        def encoder(obj: object) -> str:
            fp: StringIO = StringIO()
            write: Callable[[str], object] = fp.write
            try:
                write_value(obj, write, "\n")
            except (ValueError, TypeError) as exc:
                raise exc.with_traceback(None) from None
            finally:
                markers.clear()

            write(end)
            return fp.getvalue()

        return encoder
