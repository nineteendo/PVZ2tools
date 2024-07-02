"""JSON accelerator."""
# Copyright (C) 2024 Nice Zombies
from typing import Any, Callable

from jsonc import JSONDecoder


def make_scanner(decoder: JSONDecoder) -> (
    Callable[[str, int], tuple[Any, int]]
):
    """Make JSON scanner."""


def parse_string(s: str, end: int, /) -> tuple[str, int]:
    """Parse JSON string."""
