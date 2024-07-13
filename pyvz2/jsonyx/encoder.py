# Copyright (C) 2024 Nice Zombies
"""JSON encoder."""
from __future__ import annotations

__all__: list[str] = ["JSONEncoder"]

import json
from typing import TYPE_CHECKING

from typing_extensions import Literal

if TYPE_CHECKING:
    from collections.abc import Container


# TODO(Nice Zombies): only allow strings as keys
class JSONEncoder(json.JSONEncoder):
    """JSON encoder."""

    # TODO(Nice Zombies): align_items=True
    # pylint: disable-next=R0913
    def __init__(  # noqa: PLR0913
        self,
        *,
        allow: Container[Literal["nan"] | str] = (),
        ensure_ascii: bool = False,
        indent: int | str | None = None,
        item_separator: str = ", ",
        key_separator: str = ": ",
        sort_keys: bool = False,
    ) -> None:
        """Create new JSON encoder."""
        if indent is not None:
            item_separator = item_separator.rstrip()

        super().__init__(
            ensure_ascii=ensure_ascii,
            allow_nan="nan" in allow,
            sort_keys=sort_keys,
            indent=indent,
            separators=(item_separator, key_separator),
        )
