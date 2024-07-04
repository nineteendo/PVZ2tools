# !/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""PyVZ2, a command line utility to modify PVZ2."""
from __future__ import annotations

__all__: list[str] = []

import sys
from argparse import ArgumentParser
from typing import Any, Literal, assert_never

import jsonc.tool


class _PyVZ2Namespace:  # pylint: disable=R0903
    command: Literal["json"]


def _main() -> None:
    try:
        parser: ArgumentParser = ArgumentParser()
        commands = parser.add_subparsers(
            dest="command", required=True, help="command",
        )
        jsonc.tool.configure(commands.add_parser("json"))
        args: Any = parser.parse_args()
        pyvz2_args: _PyVZ2Namespace = args
        if pyvz2_args.command == "json":
            jsonc.tool.run(args)
        else:
            assert_never(pyvz2_args.command)
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
