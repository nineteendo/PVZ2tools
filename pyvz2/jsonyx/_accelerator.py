# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): replace with jsonyx._accelerator.c
"""JSON accelerator."""
from __future__ import annotations

__all__: list[str] = ["DuplicateKey", "make_scanner", "scanstring"]

# pylint: disable-next=E0611, E0401
from _jsonyx import (  # type: ignore # isort: skip
    DuplicateKey, make_scanner, scanstring,  # type: ignore # noqa: PLC2701
)
