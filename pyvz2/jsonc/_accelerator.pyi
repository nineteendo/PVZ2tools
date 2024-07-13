# Copyright (C) 2024 Nice Zombies
"""JSON accelerator."""
__all__: list[str] = ["make_scanner", "scanstring"]

from collections.abc import Callable

from jsonc.decoder import JSONDecoder
from typing_extensions import Any


def make_scanner(context: JSONDecoder) -> (
    Callable[[str, str, int], tuple[Any, int]]
):
    """Make JSON scanner."""


def scanstring(filename: str, s: str, end: int, /) -> tuple[str, int]:
    """Scan JSON string."""
