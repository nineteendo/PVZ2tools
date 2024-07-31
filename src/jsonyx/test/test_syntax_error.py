# Copyright (C) 2024 Nice Zombies
# TODO(Nice Zombies): test position
# TODO(Nice Zombies): test __str__
"""JSONSyntaxError tests."""
from __future__ import annotations

__all__: list[str] = []


import pytest
from jsonyx import JSONSyntaxError
# pylint: disable-next=W0611
from jsonyx.test import get_json  # type: ignore # noqa: F401


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
