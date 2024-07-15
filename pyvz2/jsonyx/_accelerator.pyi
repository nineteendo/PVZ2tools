# Copyright (C) 2024 Nice Zombies
"""JSON accelerator."""
__all__: list[str] = [
    "DuplicateKey",
    "encode_basestring",
    "encode_basestring_ascii",
    "make_encoder",
    "make_scanner",
    "scanstring",
]

from collections.abc import Callable

from jsonyx.decoder import JSONDecoder
from typing_extensions import Any


def encode_basestring(s: str) -> str:
    """Return the JSON representation of a Python string."""


def encode_basestring_ascii(s: str) -> str:
    """Return the ASCII-only JSON representation of a Python string."""


def make_encoder(
    indent: str | None,
    key_separator: str,
    item_separator: str,
    allow_nan: bool,  # noqa: FBT001
    ensure_ascii: bool,  # noqa: FBT001
) -> Callable[[Any], str]:
    """Make JSON encoder."""


def make_scanner(context: JSONDecoder) -> (
    Callable[[str, str, int], tuple[Any, int]]
):
    """Make JSON scanner."""


def scanstring(filename: str, s: str, end: int, /) -> tuple[str, int]:
    """Scan JSON string."""


class DuplicateKey(str):  # noqa: SLOT000
    """Duplicate key."""
