# Copyright (C) 2024 Nice Zombies
"""JSON write tests."""
from __future__ import annotations

__all__: list[str] = []

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest
from jsonyx.allow import SURROGATES
# pylint: disable-next=W0611
from jsonyx.test import get_json  # type: ignore # noqa: F401

if TYPE_CHECKING:
    from types import ModuleType


def test_value(json: ModuleType) -> None:
    """Test JSON value."""
    with TemporaryDirectory() as tmpdir:
        filename: Path = Path(tmpdir) / "file.json"
        json.write(0, filename, end="")
        assert filename.read_text("utf_8") == "0"


@pytest.mark.parametrize(("s", "expected"), [
    ("\ud800", '"\ud800"'),
    ("\ud800$", '"\ud800$"'),
    ("\udf48", '"\udf48"'),  # noqa: PT014
])
def test_surrogates(json: ModuleType, s: str, expected: str) -> None:
    """Test surrogates."""
    with TemporaryDirectory() as tmpdir:
        filename: Path = Path(tmpdir) / "file.json"
        json.write(s, filename, allow=SURROGATES, end="")
        assert filename.read_text("utf_8", "surrogatepass") == expected


@pytest.mark.parametrize("s", ["\ud800", "\ud800$", "\udf48"])  # noqa: PT014
def test_surrogates_if_not_allowed(json: ModuleType, s: str) -> None:
    """Test surrogates."""
    with TemporaryDirectory() as tmpdir, pytest.raises(UnicodeEncodeError):
        json.write(s, Path(tmpdir) / "file.json")
