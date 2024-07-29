# Copyright (C) 2024 Nice Zombies
"""JSONYX module for JSON (de)serialization."""
from __future__ import annotations

__all__: list[str] = [
    "Decoder",
    "DuplicateKey",
    "Encoder",
    "JSONSyntaxError",
    "detect_encoding",
    "dump",
    "dumps",
    "format_syntax_error",
    "load",
    "loads",
    "read",
    "write",
]

from codecs import (
    BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE,
)
from decimal import Decimal
from io import StringIO
from os.path import realpath
from pathlib import Path
from typing import TYPE_CHECKING

from jsonyx._decoder import DuplicateKey, JSONSyntaxError, make_scanner
from jsonyx._encoder import make_writer
from jsonyx.allow import NOTHING
from typing_extensions import Any, Literal  # type: ignore

if TYPE_CHECKING:
    from collections.abc import Callable, Container

    from _typeshed import StrPath, SupportsRead, SupportsWrite

    _AllowList = Container[Literal[
        "comments", "duplicate_keys", "missing_commas", "nan_and_infinity",
        "surrogates", "trailing_comma",
    ] | str]

try:
    from _jsonyx import make_encoder
except ImportError:
    make_encoder = None


def detect_encoding(b: bytearray | bytes) -> str:
    """Detect JSON encoding."""
    # JSON must start with ASCII character (not NULL)
    # Strings can't contain control characters (including NULL)
    encoding: str = "utf_8"
    startswith: Callable[[bytes | tuple[bytes, ...]], bool] = b.startswith
    if startswith((BOM_UTF32_BE, BOM_UTF32_LE)):
        encoding = "utf_32"
    elif startswith((BOM_UTF16_BE, BOM_UTF16_LE)):
        encoding = "utf_16"
    elif startswith(BOM_UTF8):
        encoding = "utf_8_sig"
    elif len(b) >= 4:
        if not b[0]:
            # 00 00 -- -- - utf_32_be
            # 00 XX -- -- - utf_16_be
            encoding = "utf_16_be" if b[1] else "utf_32_be"
        elif not b[1]:
            # XX 00 00 00 - utf_32_le
            # XX 00 00 XX - utf_16_le
            # XX 00 XX -- - utf_16_le
            encoding = "utf_16_le" if b[2] or b[3] else "utf_32_le"
    elif len(b) == 2:
        if not b[0]:
            # 00 -- - utf_16_be
            encoding = "utf_16_be"
        elif not b[1]:
            # XX 00 - utf_16_le
            encoding = "utf_16_le"

    return encoding


class Decoder:
    """JSON decoder."""

    def __init__(
        self,
        *,
        allow: _AllowList = NOTHING,
        use_decimal: bool = False,
    ) -> None:
        """Create new JSON decoder."""
        allow_surrogates: bool = "surrogates" in allow
        self._errors: str = "surrogatepass" if allow_surrogates else "strict"
        self._scanner: Callable[[str, str], tuple[Any]] = make_scanner(
            "comments" in allow, "duplicate_keys" in allow,
            "missing_commas" in allow, "nan_and_infinity" in allow,
            allow_surrogates, "trailing_comma" in allow, use_decimal,
        )

    def read(self, filename: StrPath) -> Any:
        """Deserialize a JSON file to a Python object."""
        with Path(filename).open("rb") as fp:
            self.loads(fp.read(), filename=filename)

    def load(
        self, fp: SupportsRead[bytes | str], *, filename: StrPath = "<string>",
    ) -> Any:
        """Deserialize an open JSON file to a Python object."""
        return self.loads(fp.read(), filename=getattr(fp, "name", filename))

    def loads(
        self, s: bytearray | bytes | str, *, filename: StrPath = "<string>",
    ) -> Any:
        """Deserialize a JSON string to a Python object."""
        if (
            not isinstance(filename, str)
            or (not filename.startswith("<") and not filename.endswith(">"))
        ):
            filename = realpath(filename)

        if not isinstance(s, str):
            s = s.decode(detect_encoding(s), self._errors)
        elif s.startswith("\ufeff"):
            msg: str = "Unexpected UTF-8 BOM"
            raise JSONSyntaxError(msg, filename, s, 0)

        return self._scanner(filename, s)


class Encoder:
    """JSON encoder."""

    # TODO(Nice Zombies): add trailing_comma=True
    # pylint: disable-next=R0913
    def __init__(  # noqa: PLR0913
        self,
        *,
        allow: _AllowList = NOTHING,
        ensure_ascii: bool = False,
        indent: int | str | None = None,
        item_separator: str = ", ",
        key_separator: str = ": ",
        sort_keys: bool = False,
    ) -> None:
        """Create new JSON encoder."""
        allow_nan_and_infinity: bool = "nan_and_infinity" in allow
        allow_surrogates: bool = "surrogates" in allow
        decimal_str: Callable[[Decimal], str] = Decimal.__str__

        def encode_decimal(decimal: Decimal) -> str:
            if not decimal.is_finite():
                if decimal.is_snan():
                    msg: str = f"{decimal!r} is not JSON serializable"
                    raise ValueError(msg)

                if not allow_nan_and_infinity:
                    msg = f"{decimal!r} is not allowed"
                    raise ValueError(msg)

                if decimal.is_qnan():
                    return "NaN"

            return decimal_str(decimal)

        if indent is not None:
            item_separator = item_separator.rstrip()
            if isinstance(indent, int):
                indent = " " * indent

        if make_encoder is None:
            self._encoder: Callable[[Any], str] | None = None
        else:
            self._encoder = make_encoder(
                encode_decimal, indent, item_separator, key_separator,
                allow_nan_and_infinity, allow_surrogates, ensure_ascii,
                sort_keys,
            )

        # TODO(Nice Zombies): implement writer in C
        self._writer: Callable[[Any, SupportsWrite[str]], None] = make_writer(
            encode_decimal, indent, item_separator, key_separator,
            allow_nan_and_infinity, allow_surrogates, ensure_ascii, sort_keys,
        )

    def write(self, obj: Any, path: StrPath) -> None:
        """Serialize a Python object to a JSON file."""
        with Path(path).open("w", encoding="utf_8") as fp:
            self._writer(obj, fp)

    def dump(self, obj: Any, fp: SupportsWrite[str]) -> None:
        """Serialize a Python object to an open JSON file."""
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
    selection_length: int = exc.end_offset - exc.offset  # type: ignore
    caret_line: str = (  # type: ignore
        " " * (exc.offset - 1) + "^" * selection_length  # type: ignore
    )
    exc_type: type[JSONSyntaxError] = type(exc)
    # TODO(Nice Zombies): include exc.end_lineno and exc.end_colno
    return f"""\
  File {exc.filename!r}, line {exc.lineno:d}, column {exc.colno:d}
    {exc.text}
    {caret_line}
{exc_type.__module__}.{exc_type.__qualname__}: {exc.msg}\
"""


def read(
    path: StrPath, *, allow: _AllowList = NOTHING, use_decimal: bool = False,
) -> Any:
    """Deserialize a JSON file to a Python object."""
    return Decoder(allow=allow, use_decimal=use_decimal).read(path)


def load(
    fp: SupportsRead[bytes | str],
    *,
    allow: _AllowList = NOTHING,
    filename: StrPath = "<string>",
    use_decimal: bool = False,
) -> Any:
    """Deserialize an open JSON file to a Python object."""
    return Decoder(allow=allow, use_decimal=use_decimal).load(
        fp, filename=filename,
    )


def loads(
    s: bytearray | bytes | str,
    *,
    allow: _AllowList = NOTHING,
    filename: StrPath = "<string>",
    use_decimal: bool = False,
) -> Any:
    """Deserialize a JSON string to a Python object."""
    return Decoder(allow=allow, use_decimal=use_decimal).loads(
        s, filename=filename,
    )


# pylint: disable-next=R0913
def write(  # noqa: PLR0913
    obj: Any,
    path: StrPath,
    *,
    allow: _AllowList = NOTHING,
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
    sort_keys: bool = False,
) -> None:
    """Serialize a Python object to a JSON file."""
    return Encoder(
        allow=allow,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
        sort_keys=sort_keys,
    ).write(obj, path)


# pylint: disable-next=R0913
def dump(  # noqa: PLR0913
    obj: Any,
    fp: SupportsWrite[str],
    *,
    allow: _AllowList = NOTHING,
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
) -> None:
    """Serialize a Python object to an open JSON file."""
    Encoder(
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
    allow: _AllowList = NOTHING,
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
    sort_keys: bool = False,
) -> str:
    """Serialize a Python object to a JSON string."""
    return Encoder(
        allow=allow,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
        sort_keys=sort_keys,
    ).dumps(obj)
