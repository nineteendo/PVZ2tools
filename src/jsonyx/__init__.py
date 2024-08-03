# Copyright (C) 2024 Nice Zombies
"""jsonyx module for JSON (de)serialization."""
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
from os import fspath
from os.path import realpath
from pathlib import Path
from sys import stdout
from typing import TYPE_CHECKING, Any, Literal

from jsonyx._decoder import DuplicateKey, JSONSyntaxError, make_scanner
from jsonyx._encoder import make_encoder
from jsonyx.allow import NOTHING

if TYPE_CHECKING:
    from collections.abc import Callable, Container

    from _typeshed import StrPath, SupportsRead, SupportsWrite

    _AllowList = Container[Literal[
        "comments", "duplicate_keys", "missing_commas", "nan_and_infinity",
        "surrogates", "trailing_comma",
    ] | str]


class Decoder:
    """JSON decoder."""

    def __init__(
        self, *, allow: _AllowList = NOTHING, use_decimal: bool = False,
    ) -> None:
        """Create a new JSON decoder.

        :param allow: the allowed JSON deviations, defaults to NOTHING
        :type allow: Container[str], optional
        :param use_decimal: use decimal instead of float, defaults to False
        :type use_decimal: bool, optional
        """
        allow_surrogates: bool = "surrogates" in allow
        self._errors: str = "surrogatepass" if allow_surrogates else "strict"
        self._scanner: Callable[[str, str], tuple[Any]] = make_scanner(
            "comments" in allow, "duplicate_keys" in allow,
            "missing_commas" in allow, "nan_and_infinity" in allow,
            allow_surrogates, "trailing_comma" in allow, use_decimal,
        )

    def read(self, filename: StrPath) -> Any:
        """Deserialize a JSON file to a Python object.

        :param filename: the path to the JSON file
        :type filename: StrPath
        :raises JSONSyntaxError: if the JSON file is invalid
        :return: a Python object
        :rtype: Any
        """
        return self.loads(Path(filename).read_bytes(), filename=filename)

    def load(
        self, fp: SupportsRead[bytes | str], *, root: StrPath = ".",
    ) -> Any:
        """Deserialize an open JSON file to a Python object.

        :param fp: an open JSON file
        :type fp: SupportsRead[bytes | str]
        :param root: the path to the archive containing this JSON file,
                     defaults to "."
        :type root: StrPath, optional
        :raises JSONSyntaxError: if the JSON file is invalid
        :return: a Python object
        :rtype: Any
        """
        name: str | None
        if name := getattr(fp, "name", None):
            return self.loads(fp.read(), filename=Path(root) / name)

        return self.loads(fp.read())

    def loads(
        self, s: bytearray | bytes | str, *, filename: StrPath = "<string>",
    ) -> Any:
        """Deserialize a JSON string to a Python object.

        :param s: a JSON string
        :type s: bytearray | bytes | str
        :param filename: the path to the JSON file, defaults to "<string>"
        :type filename: StrPath, optional
        :raises JSONSyntaxError: if the JSON string is invalid
        :return: a Python object
        :rtype: Any
        """
        filename = fspath(filename)
        if not filename.startswith("<") and not filename.endswith(">"):
            filename = realpath(filename)

        if not isinstance(s, str):
            s = s.decode(detect_encoding(s), self._errors)
        elif s.startswith("\ufeff"):
            msg: str = "Unexpected UTF-8 BOM"
            raise JSONSyntaxError(msg, filename, s, 0)

        return self._scanner(filename, s)


class Encoder:
    """JSON encoder."""

    # pylint: disable-next=R0913
    def __init__(  # noqa: PLR0913
        self,
        *,
        allow: _AllowList = NOTHING,
        end: str = "\n",
        ensure_ascii: bool = False,
        indent: int | str | None = None,
        item_separator: str = ", ",
        key_separator: str = ": ",
        sort_keys: bool = False,
        trailing_comma: bool = False,
    ) -> None:
        r"""Create a new JSON encoder.

        :param allow: the allowed JSON deviations, defaults to NOTHING
        :type allow: Container[str], optional
        :param end: the string to append at the end, defaults to "\\n"
        :type end: str, optional
        :param ensure_ascii: escape non-ASCII characters, defaults to False
        :type ensure_ascii: bool, optional
        :param indent: indentation, defaults to None
        :type indent: int | str | None, optional
        :param item_separator: the separator between two items, defaults to
                               ", "
        :type item_separator: str, optional
        :param key_separator: the separator between a key and a value, defaults
                              to ": "
        :type key_separator: str, optional
        :param sort_keys: sort the keys of objects, defaults to False
        :type sort_keys: bool, optional
        :param trailing_comma: add a trailing comma if indented, defaults to
                               False
        :type trailing_comma: bool, optional
        """
        allow_nan_and_infinity: bool = "nan_and_infinity" in allow
        allow_surrogates: bool = "surrogates" in allow
        decimal_str: Callable[[Decimal], str] = Decimal.__str__

        if indent is not None:
            item_separator = item_separator.rstrip()
            if isinstance(indent, int):
                indent = " " * indent

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

        self._encoder: Callable[[object], str] = make_encoder(
            encode_decimal, indent, end, item_separator, key_separator,
            allow_nan_and_infinity, allow_surrogates, ensure_ascii, sort_keys,
            trailing_comma,
        )
        self._errors: str = "surrogatepass" if allow_surrogates else "strict"

    def write(self, obj: object, filename: StrPath) -> None:
        """Serialize a Python object to a JSON file.

        :param obj: a Python object
        :type obj: object
        :param filename: the path to the JSON file
        :type filename: StrPath
        :raises ValueError: for invalid values
        :raises TypeError: for unserializable values
        """
        Path(filename).write_text(self._encoder(obj), "utf_8", self._errors)

    def dump(self, obj: object, fp: SupportsWrite[str] = stdout) -> None:
        """Serialize a Python object to an open JSON file.

        :param obj: a Python object
        :type obj: object
        :param fp: an open JSON file, defaults to stdout
        :type fp: SupportsWrite[str], optional
        :raises ValueError: for invalid values
        :raises TypeError: for unserializable values
        """
        fp.write(self._encoder(obj))

    def dumps(self, obj: object) -> str:
        """Serialize a Python object to a JSON string.

        :param obj: a Python object
        :type obj: object
        :raises ValueError: for invalid values
        :raises TypeError: for unserializable values
        :return: a JSON string
        :rtype: str
        """
        return self._encoder(obj)


def detect_encoding(b: bytearray | bytes) -> str:
    """Detect JSON encoding.

    :param b: a JSON string
    :type b: bytearray | bytes
    :return: the detected encoding
    :rtype: str
    """
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


def format_syntax_error(exc: JSONSyntaxError) -> list[str]:
    """Format JSON syntax error.

    :param exc: a JSON syntax error
    :type exc: JSONSyntaxError
    :return: a list of strings, each ending in a newline
    :rtype: list[str]
    """
    if exc.end_lineno == exc.lineno:
        line_range: str = f"{exc.lineno:d}"
    else:
        line_range = f"{exc.lineno:d}-{exc.end_lineno:d}"

    if exc.end_colno == exc.colno:
        column_range: str = f"{exc.colno:d}"
    else:
        column_range = f"{exc.colno:d}-{exc.end_colno:d}"

    caret_indent: str = " " * (exc.offset - 1)  # type: ignore
    caret_selection: str = "^" * (exc.end_offset - exc.offset)  # type: ignore
    return [
        f'  File "{exc.filename}", line {line_range}, column {column_range}\n',
        f"    {exc.text}\n",
        f"    {caret_indent}{caret_selection}\n",
        f"{exc.__module__}.{type(exc).__qualname__}: {exc.msg}\n",
    ]


def read(
    filename: StrPath,
    *,
    allow: _AllowList = NOTHING,
    use_decimal: bool = False,
) -> Any:
    """Deserialize a JSON file to a Python object.

    :param filename: the path to the JSON file
    :type filename: StrPath
    :param allow: the allowed JSON deviations, defaults to NOTHING
    :type allow: Container[str], optional
    :param use_decimal: use decimal instead of float, defaults to False
    :type use_decimal: bool, optional
    :raises JSONSyntaxError: if the JSON file is invalid
    :return: a Python object.
    :rtype: Any
    """
    return Decoder(allow=allow, use_decimal=use_decimal).read(filename)


def load(
    fp: SupportsRead[bytes | str],
    *,
    allow: _AllowList = NOTHING,
    root: StrPath = ".",
    use_decimal: bool = False,
) -> Any:
    """Deserialize an open JSON file to a Python object.

    :param fp: an open JSON file
    :type fp: SupportsRead[bytes | str]
    :param allow: the allowed JSON deviations, defaults to NOTHING
    :type allow: Container[str], optional
    :param root: the path to the archive containing this JSON file, defaults to
                 "."
    :type root: StrPath, optional
    :param use_decimal: use decimal instead of float, defaults to False
    :type use_decimal: bool, optional
    :raises JSONSyntaxError: if the JSON file is invalid
    :return: a Python object
    :rtype: Any
    """
    return Decoder(allow=allow, use_decimal=use_decimal).load(fp, root=root)


def loads(
    s: bytearray | bytes | str,
    *,
    allow: _AllowList = NOTHING,
    filename: StrPath = "<string>",
    use_decimal: bool = False,
) -> Any:
    """Deserialize a JSON string to a Python object.

    :param s: a JSON string
    :type s: bytearray | bytes | str
    :param allow: the allowed JSON deviations, defaults to NOTHING
    :type allow: Container[str], optional
    :param filename: the path to the JSON file, defaults to "<string>"
    :type filename: StrPath, optional
    :param use_decimal: use decimal instead of float, defaults to False
    :type use_decimal: bool, optional
    :raises JSONSyntaxError: if the JSON string is invalid
    :return: a Python object
    :rtype: Any
    """
    return Decoder(allow=allow, use_decimal=use_decimal).loads(
        s, filename=filename,
    )


# pylint: disable-next=R0913
def write(  # noqa: PLR0913
    obj: object,
    filename: StrPath,
    *,
    allow: _AllowList = NOTHING,
    end: str = "\n",
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
    sort_keys: bool = False,
    trailing_comma: bool = False,
) -> None:
    r"""Serialize a Python object to a JSON file.

    :param obj: a Python object
    :type obj: object
    :param filename: the path to the JSON file
    :type filename: StrPath
    :param allow: the allowed JSON deviations, defaults to NOTHING
    :type allow: Container[str], optional
    :param end: the string to append at the end, defaults to "\\n"
    :type end: str, optional
    :param ensure_ascii: escape non-ASCII characters, defaults to False
    :type ensure_ascii: bool, optional
    :param indent: indentation, defaults to None
    :type indent: int | str | None, optional
    :param item_separator: the separator between two items, defaults to ", "
    :type item_separator: str, optional
    :param key_separator: the separator between a key and a value, defaults to
                          ": "
    :type key_separator: str, optional
    :param sort_keys: sort the keys of objects, defaults to False
    :type sort_keys: bool, optional
    :param trailing_comma: add a trailing comma if indented, defaults to False
    :type trailing_comma: bool, optional
    :raises ValueError: for invalid values
    :raises TypeError: for unserializable values
    """
    return Encoder(
        allow=allow,
        end=end,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
        sort_keys=sort_keys,
        trailing_comma=trailing_comma,
    ).write(obj, filename)


# pylint: disable-next=R0913
def dump(  # noqa: PLR0913
    obj: object,
    fp: SupportsWrite[str] = stdout,
    *,
    allow: _AllowList = NOTHING,
    end: str = "\n",
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
    sort_keys: bool = False,
    trailing_comma: bool = False,
) -> None:
    r"""Serialize a Python object to an open JSON file.

    :param obj: a Python object
    :type obj: object
    :param fp: an open JSON file, defaults to stdout
    :type fp: SupportsWrite[str], optional
    :param allow: the allowed JSON deviations, defaults to NOTHING
    :type allow: Container[str], optional
    :param end: the string to append at the end, defaults to "\\n"
    :type end: str, optional
    :param ensure_ascii: escape non-ASCII characters, defaults to False
    :type ensure_ascii: bool, optional
    :param indent: indentation, defaults to None
    :type indent: int | str | None, optional
    :param item_separator: the separator between two items, defaults to ", "
    :type item_separator: str, optional
    :param key_separator: the separator between a key and a value, defaults to
                          ": "
    :type key_separator: str, optional
    :param sort_keys: sort the keys of objects, defaults to False
    :type sort_keys: bool, optional
    :param trailing_comma: add a trailing comma if indented, defaults to False
    :type trailing_comma: bool, optional
    :raises ValueError: for invalid values
    :raises TypeError: for unserializable values
    """
    Encoder(
        allow=allow,
        end=end,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
        sort_keys=sort_keys,
        trailing_comma=trailing_comma,
    ).dump(obj, fp)


# pylint: disable-next=R0913
def dumps(  # noqa: PLR0913
    obj: object,
    *,
    allow: _AllowList = NOTHING,
    end: str = "\n",
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    item_separator: str = ", ",
    key_separator: str = ": ",
    sort_keys: bool = False,
    trailing_comma: bool = False,
) -> str:
    r"""Serialize a Python object to a JSON string.

    :param obj: a Python object
    :type obj: object
    :param allow: the allowed JSON deviations, defaults to NOTHING
    :type allow: Container[str], optional
    :param end: the string to append at the end, defaults to "\\n"
    :type end: str, optional
    :param ensure_ascii: escape non-ASCII characters, defaults to False
    :type ensure_ascii: bool, optional
    :param indent: indentation, defaults to None
    :type indent: int | str | None, optional
    :param item_separator: the separator between two items, defaults to ", "
    :type item_separator: str, optional
    :param key_separator: the separator between a key and a value, defaults to
                          ": "
    :type key_separator: str, optional
    :param sort_keys: sort the keys of objects, defaults to False
    :type sort_keys: bool, optional
    :param trailing_comma: add a trailing comma if indented, defaults to False
    :type trailing_comma: bool, optional
    :raises ValueError: for invalid values
    :raises TypeError: for unserializable values
    :return: a JSON string
    :rtype: str
    """
    return Encoder(
        allow=allow,
        end=end,
        ensure_ascii=ensure_ascii,
        indent=indent,
        item_separator=item_separator,
        key_separator=key_separator,
        sort_keys=sort_keys,
        trailing_comma=trailing_comma,
    ).dumps(obj)
