# Copyright (C) 2024 Nice Zombies
"""JSONYX module for JSON (de)serialization."""
from __future__ import annotations

__all__: list[str] = [
    "COMMENTS",
    "DUPLICATE_KEYS",
    "EVERYTHING",
    "NAN",
    "NOTHING",
    "TRAILING_COMMA",
    "DuplicateKey",
    "JSONDecoder",
    "JSONEncoder",
    "JSONSyntaxError",
    "dump",
    "dumps",
    "format_syntax_error",
    "load",
    "loads",
]

from codecs import (
    BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE,
)
from io import StringIO
from os.path import realpath
from typing import TYPE_CHECKING

from jsonyx._decoder import DuplicateKey, JSONSyntaxError, make_scanner
from jsonyx._encoder import make_writer
from typing_extensions import Any, Literal  # type: ignore

if TYPE_CHECKING:
    from collections.abc import Callable, Container

    from _typeshed import SupportsRead, SupportsWrite

try:
    # pylint: disable-next=C0412
    from jsonyx._accelerator import make_encoder
except ImportError:
    make_encoder = None

NOTHING: frozenset[str] = frozenset()
COMMENTS: frozenset[str] = frozenset({"comments"})
DUPLICATE_KEYS: frozenset[str] = frozenset({"duplicate_keys"})
NAN: frozenset[str] = frozenset({"nan"})
TRAILING_COMMA: frozenset[str] = frozenset({"trailing_comma"})
EVERYTHING: frozenset[str] = COMMENTS | DUPLICATE_KEYS | NAN | TRAILING_COMMA


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


class JSONDecoder:
    """JSON decoder."""

    def __init__(
        self,
        *,
        allow: Container[Literal[
            "comments", "duplicate_keys", "nan", "trailing_comma",
        ] | str] = (),
    ) -> None:
        """Create new JSON decoder."""
        self._scanner: Callable[[str, str], tuple[Any]] = make_scanner(
            "comments" in allow, "duplicate_keys" in allow, "nan" in allow,
            "trailing_comma" in allow,
        )

    def load(
        self,
        fp: SupportsRead[bytearray | bytes | str],
        *,
        filename: str = "<string>",
    ) -> Any:
        """Deserialize a JSON file to a Python object."""
        return self.loads(fp.read(), filename=getattr(fp, "name", filename))

    def loads(
        self, s: bytearray | bytes | str, *, filename: str = "<string>",
    ) -> Any:
        """Deserialize a JSON string to a Python object."""
        if not filename.startswith("<") and not filename.endswith(">"):
            filename = realpath(filename)

        if not isinstance(s, str):
            s = _decode_bytes(s)
        elif s.startswith("\ufeff"):
            msg: str = "Unexpected UTF-8 BOM"
            raise JSONSyntaxError(msg, filename, s, 0)

        return self._scanner(filename, s)


class JSONEncoder:
    """JSON encoder."""

    # pylint: disable-next=R0913
    def __init__(  # noqa: PLR0913
        self,
        *,
        allow: Container[Literal["nan"] | str] = (),
        ensure_ascii: bool = False,
        indent: int | str | None = None,
        item_separator: str = ", ",
        key_separator: str = ": ",
    ) -> None:
        """Create new JSON encoder."""
        if indent is not None:
            item_separator = item_separator.rstrip()
            if isinstance(indent, int):
                indent = " " * indent

        if make_encoder is None:
            self._encoder: Callable[[Any], str] | None = None
        else:
            self._encoder = make_encoder(
                indent, key_separator, item_separator, "nan" in allow,
                ensure_ascii,
            )

        self._writer: Callable[[Any, SupportsWrite[str]], None] = make_writer(
            indent, key_separator, item_separator, "nan" in allow,
            ensure_ascii,
        )

    def dump(self, obj: Any, fp: SupportsWrite[str]) -> None:
        """Serialize a Python object to a JSON file."""
        self._writer(obj, fp)

    def dumps(self, obj: Any) -> str:
        """Serialize a Python object to a JSON string."""
        if self._encoder:
            return self._encoder(obj)

        fp: StringIO = StringIO()
        self._writer(obj, fp)
        return fp.getvalue()


def format_syntax_error(exc: JSONSyntaxError) -> str:
    """Format JSON syntax error."""
    caret_line: str = " " * (exc.offset - 1) + "^"  # type: ignore
    exc_type: type[JSONSyntaxError] = type(exc)
    return f"""\
  File {exc.filename!r}, line {exc.lineno:d}, column {exc.colno:d}
    {exc.text}
    {caret_line}
{exc_type.__module__}.{exc_type.__qualname__}: {exc.msg}\
"""


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
) -> None:
    """Serialize a Python object to a JSON file."""
    JSONEncoder(
        allow=allow,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
    ).dump(obj, fp)


# pylint: disable-next=R0913
def dumps(  # noqa: PLR0913
    obj: Any,
    *,
    allow: Container[Literal["nan"] | str] = (),
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
) -> str:
    """Serialize a Python object to a JSON string."""
    return JSONEncoder(
        allow=allow,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
    ).dumps(obj)


def load(
    fp: SupportsRead[bytearray | bytes | str],
    *,
    allow: Container[
        Literal["comments", "duplicate_keys", "nan", "trailing_comma"] | str
    ] = (),
    filename: str = "<string>",
) -> Any:
    """Deserialize a JSON file to a Python object."""
    return JSONDecoder(allow=allow).load(fp, filename=filename)


def loads(
    s: bytearray | bytes | str,
    *,
    allow: Container[
        Literal["comments", "duplicate_keys", "nan", "trailing_comma"] | str
    ] = (),
    filename: str = "<string>",
) -> Any:
    """Deserialize a JSON string to a Python object."""
    return JSONDecoder(allow=allow).loads(s, filename=filename)
