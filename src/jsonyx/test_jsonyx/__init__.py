# Copyright (C) 2024 Nice Zombies
"""JSON tests."""
from __future__ import annotations

__all__: list[str] = ["get_json"]

from test.support.import_helper import import_fresh_module  # type: ignore
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

cjson: ModuleType | None = import_fresh_module("jsonyx", fresh=["_jsonyx"])
pyjson: ModuleType | None = import_fresh_module("jsonyx", blocked=["_jsonyx"])


@pytest.fixture(params=[cjson, pyjson], ids=["cjson", "pyjson"], name="json")
def get_json(request: pytest.FixtureRequest) -> ModuleType:
    """Get JSON module."""
    result: ModuleType | None = request.param
    if result is None:
        pytest.skip("requires _jsonyx")

    return result
