#!/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""A command line utility to modify PVZ2."""
from __future__ import annotations

__all__: list[str] = []

import sys
from argparse import ArgumentParser
from typing import Literal, cast

import jsonyx.tool
from jsonyx.tool import JSONNamespace


# pylint: disable-next=R0903
class _PyVZ2Namespace:
    command: Literal["json"]


def _main() -> None:
    parser: ArgumentParser = ArgumentParser(
        description="a command line utility to modify PVZ2.",
    )
    commands = parser.add_subparsers(
        dest="command", required=True, help="command",
    )
    jsonyx.tool.register(commands.add_parser(
        "json",
        help="a command line utility to validate and pretty-print JSON "
             "objects.",
        description="a command line utility to validate and pretty-print JSON "
                    "objects.",
    ))
    args: _PyVZ2Namespace = parser.parse_args(namespace=_PyVZ2Namespace())
    try:
        if args.command == "json":
            jsonyx.tool.run(cast(JSONNamespace, args))
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
