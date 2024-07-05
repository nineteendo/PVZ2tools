# Copyright (C) 2024 Nice Zombies
"""JSON accelerator."""
__all__: list[str] = ["make_scanner", "parse_string"]

from collections.abc import Callable
from typing import Any

from jsonc.decoder import JSONDecoder


def make_scanner(decoder: JSONDecoder) -> (
    Callable[[str, str, int], tuple[Any, int]]
):
    """Make JSON scanner."""


def parse_string(filename: str, s: str, end: int, /) -> tuple[str, int]:
    """Parse JSON string."""
