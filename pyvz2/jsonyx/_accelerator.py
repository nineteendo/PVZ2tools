# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): replace with jsonyx._accelerator.c
"""JSON accelerator."""
from __future__ import annotations

__all__: list[str] = [
    "DuplicateKey",
    "encode_basestring",
    "encode_basestring_ascii",
    "make_encoder",
    "make_scanner",
    "scanstring",
]

# pylint: disable-next=E0611, E0401
from _jsonyx import (  # type: ignore # isort: skip
    DuplicateKey, encode_basestring,  # type: ignore # noqa: PLC2701
    encode_basestring_ascii,  # type: ignore # noqa: PLC2701
    make_encoder, make_scanner, scanstring,  # type: ignore # noqa: PLC2701
)
