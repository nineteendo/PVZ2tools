# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): replace with _jsonc
"""JSON accelerator."""
from __future__ import annotations

__all__: list[str] = ["make_scanner", "scanstring"]

# pylint: disable-next=E0611, E0401
from _jsonc import make_scanner, scanstring  # type: ignore # noqa: PLC2701
