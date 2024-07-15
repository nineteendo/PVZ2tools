#!/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""PyVZ2, a command line utility to modify PVZ2."""
from __future__ import annotations

__all__: list[str] = []

import sys
from argparse import ArgumentParser
from typing import cast

import jsonyx.tool
from jsonyx.tool import JSONNamespace
from typing_extensions import Literal, assert_never  # type: ignore


class _PyVZ2Namespace:  # pylint: disable=R0903
    command: Literal["json"]


def _main() -> None:
    parser: ArgumentParser = ArgumentParser()
    commands = parser.add_subparsers(
        dest="command", required=True, help="command",
    )
    jsonyx.tool.register(commands.add_parser("json"))
    args: _PyVZ2Namespace = parser.parse_args(namespace=_PyVZ2Namespace())
    try:
        if args.command == "json":
            jsonyx.tool.run(cast(JSONNamespace, args))
        else:
            assert_never(args.command)
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
