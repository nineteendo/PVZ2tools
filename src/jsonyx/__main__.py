#!/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""A command line utility to validate and pretty-print JSON objects."""
from __future__ import annotations

__all__: list[str] = []

import sys
from argparse import ArgumentParser

from jsonyx.tool import JSONNamespace, register, run


def _main() -> None:
    parser: ArgumentParser = ArgumentParser(
        description="a command line utility to validate and pretty-print JSON "
                    "objects.",
    )
    register(parser)
    try:
        run(parser.parse_args(namespace=JSONNamespace()))
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
