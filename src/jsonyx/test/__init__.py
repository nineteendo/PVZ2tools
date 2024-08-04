# Copyright (C) 2024 Nice Zombies
"""Get JSON module."""
from __future__ import annotations

__all__: list[str] = ["get_json"]
__version__: str = "1.2.1"

from test.support.import_helper import import_fresh_module  # type: ignore
from typing import TYPE_CHECKING

import pytest

from jsonyx import JSONSyntaxError

if TYPE_CHECKING:
    from types import ModuleType

pyjson: ModuleType | None = import_fresh_module("jsonyx", blocked=["_jsonyx"])
if cjson := import_fresh_module("jsonyx", fresh=["_jsonyx"]):
    # JSONSyntaxError is cached inside the _jsonyx module
    cjson.JSONSyntaxError = JSONSyntaxError  # type: ignore


@pytest.fixture(params=[cjson, pyjson], ids=["cjson", "pyjson"], name="json")
def get_json(request: pytest.FixtureRequest) -> ModuleType:
    """Get JSON module."""
    json: ModuleType | None
    if (json := request.param) is None:
        pytest.xfail("module unavailable")
        pytest.fail("module unavailable")

    return json  # type: ignore[no-any-return]
