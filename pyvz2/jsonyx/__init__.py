# Copyright (C) 2024 Nice Zombies
"""JSONYX module."""
from __future__ import annotations

__all__: list[str] = ["dump", "dumps", "load", "loads"]

from codecs import (
    BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE,
)
from os.path import realpath
from typing import TYPE_CHECKING

from typing_extensions import Any, Literal

from jsonyx.decoder import JSONDecoder
from jsonyx.encoder import JSONEncoder
from jsonyx.scanner import JSONSyntaxError

if TYPE_CHECKING:
    from collections.abc import Callable, Container

    from _typeshed import SupportsRead, SupportsWrite


# pylint: disable-next=R0913
def dump(  # noqa: PLR0913
    obj: Any,
    fp: SupportsWrite[str],
    *,
    allow: Container[Literal["nan"] | str] = (),
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
    sort_keys: bool = False,
) -> None:
    """Serialize object to a JSON formatted file."""
    for chunk in JSONEncoder(
        allow=allow,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
        sort_keys=sort_keys,
    ).iterencode(obj):
        fp.write(chunk)


# pylint: disable-next=R0913
def dumps(  # noqa: PLR0913
    obj: Any,
    *,
    allow: Container[Literal["nan"] | str] = (),
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
    sort_keys: bool = False,
) -> str:
    """Serialize object to a JSON formatted string."""
    return JSONEncoder(
        allow=allow,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
        sort_keys=sort_keys,
    ).encode(obj)


def _decode_bytes(b: bytearray | bytes) -> str:
    encoding: str = "utf-8"
    startswith: Callable[[bytes | tuple[bytes, ...]], bool] = b.startswith
    if startswith((BOM_UTF32_BE, BOM_UTF32_LE)):
        encoding = "utf-32"
    elif startswith((BOM_UTF16_BE, BOM_UTF16_LE)):
        encoding = "utf-16"
    elif startswith(BOM_UTF8):
        encoding = "utf-8-sig"
    elif len(b) >= 4:
        if not b[0]:
            # 00 00 -- -- - utf-32-be
            # 00 XX -- -- - utf-16-be
            encoding = "utf-16-be" if b[1] else "utf-32-be"
        elif not b[1]:
            # XX 00 00 00 - utf-32-le
            # XX 00 00 XX - utf-16-le
            # XX 00 XX -- - utf-16-le
            encoding = "utf-16-le" if b[2] or b[3] else "utf-32-le"
    elif len(b) == 2:
        if not b[0]:
            # 00 XX - utf-16-be
            encoding = "utf-16-be"
        elif not b[1]:
            # XX 00 - utf-16-le
            encoding = "utf-16-le"

    return b.decode(encoding, "surrogatepass")


def load(
    fp: SupportsRead[bytearray | bytes | str],
    *,
    allow: Container[
        Literal["comments", "duplicate_keys", "nan", "trailing_comma"] | str
    ] = (),
) -> Any:
    """Deserialize a JSON file to a Python object."""
    return loads(
        fp.read(), allow=allow, filename=getattr(fp, "name", "<string>"),
    )


def loads(
    s: bytearray | bytes | str,
    *,
    allow: Container[
        Literal["comments", "duplicate_keys", "nan", "trailing_comma"] | str
    ] = (),
    filename: str = "<string>",
) -> Any:
    """Deserialize a JSON document to a Python object."""
    if not filename.startswith("<") and not filename.endswith(">"):
        filename = realpath(filename)

    if not isinstance(s, str):
        s = _decode_bytes(s)
    elif s.startswith("\ufeff"):
        msg: str = "Unexpected UTF-8 BOM"
        raise JSONSyntaxError(msg, filename, s, 0)

    return JSONDecoder(allow=allow).decode(s, filename=filename)
