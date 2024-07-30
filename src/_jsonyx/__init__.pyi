# Copyright (C) 2024 Nice Zombies
"""JSON speedups."""
__all__: list[str] = ["DuplicateKey", "make_encoder", "make_scanner"]

from collections.abc import Callable
from decimal import Decimal

from typing_extensions import Any  # type: ignore


class DuplicateKey(str):  # noqa: SLOT000
    """Duplicate key."""


def make_encoder(  # noqa: PLR0917, PLR0913
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
) -> Callable[[Any], str]:
    """Make JSON encoder."""


def make_scanner(  # noqa: PLR0913, PLR0917
    allow_comments: bool,  # noqa: FBT001
    allow_duplicate_keys: bool,  # noqa: FBT001
    allow_missing_commas: bool,  # noqa: FBT001
    allow_nan_and_infinity: bool,  # noqa: FBT001
    allow_surrogates: bool,  # noqa: FBT001
    allow_trailing_comma: bool,  # noqa: FBT001
    use_decimal: bool,  # noqa: FBT001
) -> Callable[[str, str], Any]:
    """Make JSON scanner."""
