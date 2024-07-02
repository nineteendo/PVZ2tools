"""JSON accelerator."""
# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): replace with _jsonc
from __future__ import annotations

__all__: list[str] = ["make_scanner", "parse_string"]

# pylint:disable=import-error, no-name-in-module
from _jsonc import make_scanner, parse_string  # type: ignore # noqa: PLC2701
