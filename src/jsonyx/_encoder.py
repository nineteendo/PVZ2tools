# Copyright (C) 2024 Nice Zombies
"""JSON encoder."""
from __future__ import annotations

__all__: list[str] = ["make_writer"]

import re
from math import inf
from re import Match, Pattern
from typing import TYPE_CHECKING

from typing_extensions import Any  # type: ignore

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from _typeshed import SupportsWrite


_ESCAPE: Pattern[str] = re.compile(r'["\\\x00-\x1f]')
_ESCAPE_ASCII: Pattern[str] = re.compile(r'(?:["\\]|[^\x20-\x7e])')
_ESCAPE_DCT: dict[str, str] = {chr(i): f"\\u{i:04x}" for i in range(0x20)} | {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}

try:
    from jsonyx._accelerator import encode_basestring, encode_basestring_ascii
except ImportError:
    def encode_basestring(s: str) -> str:
        """Return the JSON representation of a Python string."""
        return f'"{_ESCAPE.sub(lambda match: _ESCAPE_DCT[match.group()], s)}"'

    def encode_basestring_ascii(s: str) -> str:
        """Return the ASCII-only JSON representation of a Python string."""
        def replace(match: Match[str]) -> str:
            s: str = match.group()
            try:
                return _ESCAPE_DCT[s]
            except KeyError:
                uni: int = ord(s)
                if 0xd800 <= uni <= 0xdfff:
                    msg: str = f"Surrogate {s!r} can not be escaped"
                    raise ValueError(msg) from None

                if uni < 0x10000:
                    return f"\\u{uni:04x}"

                # surrogate pair
                uni -= 0x10000
                uni1: int = 0xd800 | ((uni >> 10) & 0x3ff)
                uni2: int = 0xdc00 | (uni & 0x3ff)
                return f"\\u{uni1:04x}\\u{uni2:04x}"

        return f'"{_ESCAPE_ASCII.sub(replace, s)}"'


# pylint: disable-next=R0915, R0913
def make_writer(  # noqa: C901, PLR0915, PLR0917, PLR0913
    indent: str | None,
    key_separator: str,
    item_separator: str,
    sort_keys: bool,  # noqa: FBT001
    allow_nan: bool,  # noqa: FBT001
    ensure_ascii: bool,  # noqa: FBT001
) -> Callable[[Any, SupportsWrite[str]], None]:
    """Make JSON interencode."""
    if ensure_ascii:
        encode_string: Callable[[str], str] = encode_basestring_ascii
    else:
        encode_string = encode_basestring

    float_repr: Callable[[float], str] = float.__repr__
    int_repr: Callable[[int], str] = int.__repr__
    markers: dict[int, Any] = {}

    def floatstr(num: float) -> str:
        # pylint: disable-next=R0124
        if num != num:  # noqa: PLR0124
            text = "NaN"
        elif num == inf:
            text = "Infinity"
        elif num == -inf:
            text = "-Infinity"
        else:
            return float_repr(num)

        if not allow_nan:
            msg: str = f"{num!r} is not allowed"
            raise ValueError(msg)

        return text

    def write_list(
        lst: list[Any], write: Callable[[str], Any], old_indent: str,
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
            write(old_indent)

        write("]")

    def write_dict(
        dct: dict[Any, Any], write: Callable[[str], Any], old_indent: str,
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
        items: Iterable[tuple[Any, Any]] = (
            sorted(dct.items()) if sort_keys else dct.items()
        )
        for key, value in items:
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
            write(old_indent)

        write("}")

    def write_value(
        obj: Any, write: Callable[[str], Any], current_indent: str,
    ) -> None:
        if isinstance(obj, str):
            write(encode_string(obj))
        elif obj is None:
            write("null")
        elif obj is True:
            write("true")
        elif obj is False:
            write("false")
        elif isinstance(obj, int):
            write(int_repr(obj))
        elif isinstance(obj, float):
            write(floatstr(obj))
        elif isinstance(obj, list):
            write_list(obj, write, current_indent)  # type: ignore
        elif isinstance(obj, dict):
            write_dict(obj, write, current_indent)  # type: ignore
        else:
            msg: str = f"{type(obj).__name__} is not JSON serializable"
            raise TypeError(msg)

    def writer(obj: Any, fp: SupportsWrite[str]) -> None:
        try:
            write_value(obj, fp.write, "\n")
        except (ValueError, TypeError) as exc:
            raise exc.with_traceback(None) from exc
        finally:
            markers.clear()

    return writer
