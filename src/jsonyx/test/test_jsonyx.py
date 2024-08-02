# Copyright (C) 2024 Nice Zombies
"""JSON tests."""
from __future__ import annotations

__all__: list[str] = []

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest
from jsonyx import JSONSyntaxError, detect_encoding, format_syntax_error
# pylint: disable-next=W0611
from jsonyx.test import get_json  # type: ignore # noqa: F401

if TYPE_CHECKING:
    from types import ModuleType


def test_duplicate_key(json: ModuleType) -> None:
    """Test DuplicateKey."""
    string: object = json.DuplicateKey("")
    assert isinstance(string, str)
    assert not str(string)
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
    assert detect_encoding(bytes.fromhex(s.replace("XX", "01"))) == encoding


@pytest.mark.parametrize(("doc", "end", "line_range", "column_range"), [
    ("line 1", 5, "1", "6"),
    #      ^
    ("line 1", 6, "1", "6-7"),
    #      ^
    ("line 1\nline 2", 12, "1-2", "6"),
    #      ^^^^^^^^
    ("line 1\nline 2", 13, "1-2", "6-7"),
    #      ^^^^^^^^^
])
def test_format_syntax_error(
    doc: str, end: int, line_range: str, column_range: str,
) -> None:
    """Test format_syntax_error."""
    exc: JSONSyntaxError = JSONSyntaxError("", "<string>", doc, 5, end)
    assert format_syntax_error(exc)[0] == (
        f'  File "<string>", line {line_range}, column {column_range}\n'
    )


def test_dump(json: ModuleType) -> None:
    """Test JSON dump."""
    fp: StringIO = StringIO()
    json.dump(0, fp, end="")
    assert fp.getvalue() == "0"


def test_load(json: ModuleType) -> None:
    """Test JSON load."""
    assert json.load(StringIO("0")) == 0


def test_read(json: ModuleType) -> None:
    """Test JSON read."""
    with TemporaryDirectory() as tmpdir:
        filename: Path = Path(tmpdir) / "file.json"
        filename.write_text("0", "utf_8")
        assert json.read(filename) == 0
