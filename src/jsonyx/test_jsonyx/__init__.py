# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): test jsonyx.JSONDecoder
# TODO(Nice Zombies): test jsonyx.JSONEncoder
# TODO(Nice Zombies): test jsonyx.JSONSyntaxError
# TODO(Nice Zombies): test jsonyx.dump
# TODO(Nice Zombies): test jsonyx.dumps
# TODO(Nice Zombies): test jsonyx.format_syntax_error
# TODO(Nice Zombies): test jsonyx.load
"""JSON tests."""
from __future__ import annotations

__all__: list[str] = ["get_json"]

from test.support.import_helper import import_fresh_module  # type: ignore
from typing import TYPE_CHECKING

import pytest
from jsonyx import JSONSyntaxError, auto_decode

if TYPE_CHECKING:
    from types import ModuleType

cjson: ModuleType | None = import_fresh_module(
    "jsonyx", fresh=["jsonyx._speedups"],
)
pyjson: ModuleType | None = import_fresh_module(
    "jsonyx", blocked=["jsonyx._speedups"],
)
if cjson:
    # JSONSyntaxError is cached inside the _jsonyx module
    cjson.JSONSyntaxError = JSONSyntaxError  # type: ignore


@pytest.fixture(params=[cjson, pyjson], ids=["cjson", "pyjson"], name="json")
def get_json(request: pytest.FixtureRequest) -> ModuleType:
    """Get JSON module."""
    json: ModuleType | None = request.param
    if json is None:
        pytest.skip("requires jsonyx._speedups")

    return json


def test_duplicate_key(json: ModuleType) -> None:
    """Test DuplicateKey."""
    string: str = json.DuplicateKey("a")
    assert str(string) == "a"
    assert hash(string) == id(string)


@pytest.mark.parametrize("s", [
    "30",  # UTF-8
    "0030",  # UTF-16 (BE)
    "3000",  # UTF-16 (LE)
    "00000030",  # UTF-32 (BE)
    "30000000",  # UTF-32 (LE)

    # Byte order marks
    "ef bb bf 30",  # UTF-8
    "feff 0030",  # UTF-16 (BE)
    "fffe 3000",  # UTF-16 (LE)
    "0000feff 00000030",  # UTF-32 (BE)
    "fffe0000 30000000",  # UTF-32 (LE)
])
def test_auto_decode(s: str) -> None:
    """Test auto_decode."""
    assert auto_decode(bytes.fromhex(s)) == "0"
