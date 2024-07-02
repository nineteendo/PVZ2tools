"""JSON with Comments module."""
# Copyright (C) 2024 Nice Zombies
from __future__ import annotations

__all__: list[str] = ["JSONDecodeError", "JSONDecoder", "load", "loads"]

from codecs import (
    BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE,
)
from typing import TYPE_CHECKING, Any, Callable

from jsonc.decoder import JSONDecodeError, JSONDecoder

if TYPE_CHECKING:
    from _typeshed import SupportsRead


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


def load(fp: SupportsRead[bytes | str]) -> Any:
    """Deserialize a JSON file to a Python object."""
    return loads(fp.read())


def loads(s: bytearray | bytes | str) -> Any:
    """Deserialize a JSON document to a Python object."""
    if not isinstance(s, str):
        s = _decode_bytes(s)
    elif s.startswith("\ufeff"):
        msg: str = "Unexpected UTF-8 BOM (decode using utf-8-sig)"
        raise JSONDecodeError(msg, s, 0)

    return JSONDecoder().decode(s)
