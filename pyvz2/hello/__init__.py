"""The hello module."""
# Copyright (C) 2024 Nice Zombies
from __future__ import annotations

__all__: list[str] = ["hello_world"]

try:
    from _hello import hello_world  # type: ignore
except ImportError:
    def hello_world() -> str:
        """Return hello world."""
        return "hello world"
