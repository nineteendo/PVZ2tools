# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): test jsonyx.JSONSyntaxError
# TODO(Nice Zombies): test jsonyx.dump
# TODO(Nice Zombies): test jsonyx.format_syntax_error
# TODO(Nice Zombies): test jsonyx.load
# TODO(Nice Zombies): test jsonyx.read
# TODO(Nice Zombies): test jsonyx.write
"""JSON tests."""
from __future__ import annotations

__all__: list[str] = []

from typing import TYPE_CHECKING

import pytest
from jsonyx import detect_encoding
# pylint: disable-next=W0611
from jsonyx.test import get_json  # type: ignore # noqa: F401

if TYPE_CHECKING:
    from types import ModuleType


def test_duplicate_key(json: ModuleType) -> None:
    """Test DuplicateKey."""
    string: str = json.DuplicateKey("a")
    assert str(string) == "a"
    assert hash(string) == id(string)


@pytest.mark.parametrize(("s", "encoding"), [
    # JSON must start with ASCII character (not NULL)
    # Strings can't contain control characters (including NULL)

    # utf_8
    ("", "utf_8"),  # Empty JSON (prefer utf_8)
    ("XX", "utf_8"),  # 1 ASCII character
    ("XX XX", "utf_8"),  # 2 ASCII characters
    ("XX XX XX", "utf_8"),  # 3 ASCII characters
    ("XX XX XX XX", "utf_8"),  # 4 ASCII characters

    # utf_8_sig
    ("ef bb bf", "utf_8_sig"),  # Empty JSON with BOM
    ("ef bb bf XX", "utf_8_sig"),  # BOM + 1 ASCII character

    # utf_16_be
    ("00 XX", "utf_16_be"),  # 1 ASCII character (BE)
    ("00 XX 00 XX", "utf_16_be"),  # 2 ASCII characters (BE)
    ("00 XX XX 00", "utf_16_be"),  # 1 ASCII + 1 Unicode character (BE)
    ("00 XX XX XX", "utf_16_be"),  # 1 ASCII + 1 Unicode character (BE)

    # utf_16_le
    ("XX 00", "utf_16_le"),  # 1 ASCII character (LE)
    ("XX 00 00 XX", "utf_16_le"),  # 1 ASCII + 1 Unicode character (LE)
    ("XX 00 XX 00", "utf_16_le"),  # 2 ASCII characters (LE)
    ("XX 00 XX XX", "utf_16_le"),  # 1 ASCII + 1 Unicode character (LE)

    # utf_16
    ("fe ff", "utf_16"),  # Empty JSON with BOM (BE)
    ("fe ff 00 XX", "utf_16"),  # BOM + 1 ASCII character (BE)
    ("ff fe", "utf_16"),  # Empty JSON with BOM (LE)
    ("ff fe XX 00", "utf_16"),  # BOM + 1 ASCII character (LE)

    # utf_32_be
    ("00 00 00 XX", "utf_32_be"),  # 1 ASCII character (BE)

    # utf_32_le
    ("XX 00 00 00", "utf_32_le"),  # 1 ASCII character (LE)

    # utf_32
    ("00 00 fe ff", "utf_32"),  # Empty JSON with BOM (BE)
    ("00 00 fe ff 00 00 00 XX", "utf_32"),  # BOM + 1 ASCII character (BE)
    ("ff fe 00 00", "utf_32"),  # Empty JSON with BOM (LE)
    ("ff fe 00 00 XX 00 00 00", "utf_32"),  # BOM + 1 ASCII character (LE)
])
def test_detect_encoding(s: str, encoding: str) -> None:
    """Test detect JSON encoding."""
    b: bytes = bytes.fromhex(s.replace("XX", "01"))
    assert detect_encoding(b) == encoding
