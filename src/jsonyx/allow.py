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

#: Allow nothing
NOTHING: frozenset[str] = frozenset()
#: Allow comments
COMMENTS: frozenset[str] = frozenset({"comments"})
#: Allow duplicate keys
DUPLICATE_KEYS: frozenset[str] = frozenset({"duplicate_keys"})
#: Allow missing comma's
MISSING_COMMAS: frozenset[str] = frozenset({"missing_commas"})
#: Allow NaN and infinity
NAN_AND_INFINITY: frozenset[str] = frozenset({"nan_and_infinity"})
#: Allow trailing comma
TRAILING_COMMA: frozenset[str] = frozenset({"trailing_comma"})
#: Allow surrogates
SURROGATES: frozenset[str] = frozenset({"surrogates"})
#: Allow everything
EVERYTHING: frozenset[str] = (
    COMMENTS | DUPLICATE_KEYS | MISSING_COMMAS | NAN_AND_INFINITY | SURROGATES
    | TRAILING_COMMA
)
