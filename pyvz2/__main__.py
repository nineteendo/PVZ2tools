# !/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""PyVZ2, a command line utility to modify PVZ2."""
from __future__ import annotations

__all__: list[str] = []

import sys
from argparse import ArgumentParser, Namespace
from typing import Literal, assert_never, cast

import jsonc.tool
from jsonc.tool import JSONNamespace


class _PyVZ2Namespace(Namespace):  # pylint: disable=R0903
    command: Literal["json"]


def _main() -> None:
    try:
        parser: ArgumentParser = ArgumentParser()
        commands = parser.add_subparsers(
            dest="command", required=True, help="command",
        )
        jsonc.tool.configure(commands.add_parser("json"))
        args: _PyVZ2Namespace = parser.parse_args(namespace=_PyVZ2Namespace())
        if args.command == "json":
            jsonc.tool.run(cast(JSONNamespace, args))
        else:
            assert_never(args.command)
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
