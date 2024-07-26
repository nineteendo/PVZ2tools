# Copyright (C) 2024 Nice Zombies
"""Allow JSON deviations."""
from __future__ import annotations

__all__: list[str] = [
    "COMMENTS",
    "DUPLICATE_KEYS",
    "EVERYTHING",
    "MISSING_COMMAS",
    "NAN_AND_INFINITY",
    "NOTHING",
    "SURROGATES",
    "TRAILING_COMMA",
]

NOTHING: frozenset[str] = frozenset()
COMMENTS: frozenset[str] = frozenset({"comments"})
DUPLICATE_KEYS: frozenset[str] = frozenset({"duplicate_keys"})
MISSING_COMMAS: frozenset[str] = frozenset({"missing_commas"})
NAN_AND_INFINITY: frozenset[str] = frozenset({"nan_and_infinity"})
TRAILING_COMMA: frozenset[str] = frozenset({"trailing_comma"})
SURROGATES: frozenset[str] = frozenset({"surrogates"})
EVERYTHING: frozenset[str] = (
    COMMENTS | DUPLICATE_KEYS | MISSING_COMMAS | NAN_AND_INFINITY | SURROGATES
    | TRAILING_COMMA
)
