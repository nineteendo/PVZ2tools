# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): add more tests
"""JSON dumps tests."""
from __future__ import annotations

__all__: list[str] = []

from typing import TYPE_CHECKING

import pytest
# pylint: disable-next=W0611
from jsonyx.test import get_json  # type: ignore # noqa: F401

if TYPE_CHECKING:
    from types import ModuleType


@pytest.mark.parametrize(("obj", "expected"), [
    (True, "true"),
    (False, "false"),
    (None, "null"),
])
def test_singletons(
    json: ModuleType, obj: bool | None, expected: str,  # noqa: FBT001
) -> None:
    """Test Python singletons."""
    assert json.dumps(obj, end="") == expected
