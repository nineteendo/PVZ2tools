# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): test __str__
"""JSONSyntaxError tests."""
from __future__ import annotations

__all__: list[str] = []

import pytest
from jsonyx import JSONSyntaxError


@pytest.mark.parametrize(
    ("doc", "start", "end", "lineno", "end_lineno", "colno", "end_colno"), [
        # Offset
        ("line ", 5, -1, 1, 1, 6, 6),  # line 1, column 6
        #      ^
        ("line \nline 2", 5, -1, 1, 1, 6, 6),  # line 1, column 6
        #      ^
        ("line ?", 5, -1, 1, 1, 6, 7),  # line 1, column 6-7
        #      ^
        ("line ?\nline 2", 5, -1, 1, 1, 6, 7),  # line 1, column 6-7
        #      ^

        # Range
        ("line 1", 0, 1, 1, 1, 1, 2),  # line 1, column 1-2
        # ^
        ("line 1\nline 2", 12, 13, 2, 2, 6, 7),  # line 2, column 6-7
        #              ^
        ("line 1\nline 2\nline 3", 12, 19, 2, 3, 6, 6),  # line 2-3, column 6
        #              ^^^^^^^^
        ("line 1\nline 2\nline 3", 12, 20, 2, 3, 6, 7),  # line 2-3, column 6-7
        #              ^^^^^^^^^
    ],
)
# pylint: disable-next=R0913
def test_start_and_end_position(  # noqa: PLR0913, PLR0917
    doc: str, start: int, end: int, lineno: int, end_lineno: int, colno: int,
    end_colno: int,
) -> None:
    """Test start and end position."""
    exc: JSONSyntaxError = JSONSyntaxError("", "", doc, start, end)
    assert exc.lineno == lineno
    assert exc.end_lineno == end_lineno
    assert exc.colno == colno
    assert exc.end_colno == end_colno


@pytest.mark.parametrize(
    ("columns", "doc", "start", "end", "offset", "text", "end_offset"), {
        # Only current line
        (7, "current", 0, 7, 1, "current", 8),
        #    ^^^^^^^             ^^^^^^^
        (12, "current\nnext", 0, 7, 1, "current", 8),
        #     ^^^^^^^                   ^^^^^^^
        (16, "previous\ncurrent", 9, 16, 1, "current", 8),
        #               ^^^^^^^              ^^^^^^^

        # No newline
        (17, "start-middle-end", 0, 5, 1, "start-middle-end", 6),
        #     ^^^^^                        ^^^^^
        (8, "current\nnext", 0, 12, 1, "current", 8),
        #    ^^^^^^^^^^^^^              ^^^^^^^

        # Newline
        (8, "current", 7, 8, 8, "current", 9),
        #           ^                   ^
        (8, "current\nnext", 7, 12, 8, "current", 9),
        #           ^^^^^^                     ^

        # Expand tabs
        (8, "\tcurrent", 1, 8, 2, " current", 9),
        #      ^^^^^^^              ^^^^^^^

        # Truncate start
        (7, "start-middle-end", 5, 6, 4, "...-...", 5),  # end
        #         ^                          ^
        (12, "start-middle-end", 7, 11, 5, "...middle...", 9),  # start
        #            ^^^^                       ^^^^
        (6, "start-middle-end", 13, 16, 4, "...end", 7),  # line_end
        #                 ^^^                  ^^^
        (7, "start-middle-end", 16, 17, 7, "...end", 8),  # newline
        #                    ^                    ^

        # Truncate middle
        (13, "start-middle-end", 0, 16, 1, "start...e-end", 14),
        #     ^^^^^^^^^^^^^^^^              ^^^^^^^^^^^^^

        # Truncate end
        (8, "start-middle-end", 0, 5, 1, "start...", 6),  # line_start
        #    ^^^^^                        ^^^^^
        (7, "start-middle-end", 5, 6, 4, "...-...", 5),  # start
        #         ^                          ^
        (12, "start-middle-end", 7, 11, 5, "...middle...", 9),  # end
        #            ^^^^                       ^^^^
    },
)
# pylint: disable-next=R0913
def test_err_context(  # noqa: PLR0913, PLR0917
    monkeypatch: pytest.MonkeyPatch, columns: int, doc: str, start: int,
    end: int, offset: int, text: str, end_offset: int,
) -> None:
    """Test error context."""
    monkeypatch.setenv("COLUMNS", str(4 + columns))  # leading spaces
    exc: JSONSyntaxError = JSONSyntaxError("", "", doc, start, end)
    assert exc.offset == offset
    assert exc.text == text
    assert exc.end_offset == end_offset
