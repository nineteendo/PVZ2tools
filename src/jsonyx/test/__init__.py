# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): test jsonyx.Decoder
# TODO(Nice Zombies): test jsonyx.Encoder
# TODO(Nice Zombies): test jsonyx.JSONSyntaxError
# TODO(Nice Zombies): test jsonyx.dump
# TODO(Nice Zombies): test jsonyx.dumps
# TODO(Nice Zombies): test jsonyx.format_syntax_error
# TODO(Nice Zombies): test jsonyx.load
# TODO(Nice Zombies): test jsonyx.read
# TODO(Nice Zombies): test jsonyx.write
"""Get JSON module."""
from __future__ import annotations

__all__: list[str] = ["get_json"]

from test.support.import_helper import import_fresh_module  # type: ignore
from typing import TYPE_CHECKING

import pytest
from jsonyx import JSONSyntaxError

if TYPE_CHECKING:
    from types import ModuleType

cjson: ModuleType | None = import_fresh_module(
    "jsonyx", fresh=["_jsonyx.__init__"],
)
pyjson: ModuleType | None = import_fresh_module("jsonyx", blocked=["_jsonyx"])
if cjson:
    # JSONSyntaxError is cached inside the _jsonyx module
    cjson.JSONSyntaxError = JSONSyntaxError  # type: ignore


@pytest.fixture(params=[cjson, pyjson], ids=["cjson", "pyjson"], name="json")
def get_json(request: pytest.FixtureRequest) -> ModuleType:
    """Get JSON module."""
    json: ModuleType | None = request.param
    if json is None:
        pytest.skip("requires _jsonyx")

    return json
