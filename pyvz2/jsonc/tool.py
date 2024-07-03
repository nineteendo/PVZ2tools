# !/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""JSON tool."""
from __future__ import annotations

__all__ = ["configure", "run"]

import sys
from argparse import ArgumentParser
from pathlib import Path
from sys import stdin, stdout
from typing import Any

from jsonc import dumps, loads


class _JSONNamespace:  # pylint: disable=R0903
    allow: list[str]
    compact: bool
    ensure_ascii: bool
    indent: int | str | None
    json_file: str | None
    sort_keys: bool


def configure(parser: ArgumentParser) -> None:
    """Configure JSON tool."""
    parser.add_argument("json_file", nargs="?", default=None)
    parser.add_argument(
        "--allow", action="append", default=[], choices=["nan"],
    )
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--ensure-ascii", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--indent", default=None, type=int, metavar="SPACES")
    group.add_argument(
        "--tab",
        action="store_const",
        const="\t",
        dest="indent",
        help="indent using tabs",
    )
    parser.add_argument("--sort-keys", action="store_true")


def run(args: _JSONNamespace) -> None:
    """Run JSON tool."""
    input_json: bytes | str
    if args.json_file:
        input_json = Path(args.json_file).read_bytes()
    elif stdin.isatty():
        input_json = "\n".join(iter(input, ""))
    else:
        input_json = stdin.buffer.read()

    try:
        obj: Any = loads(input_json)
        output_json: str = dumps(
            obj,
            allow=args.allow,
            ensure_ascii=args.ensure_ascii,
            indent=args.indent,
            item_separator="," if args.compact else ", ",
            key_separator=":" if args.compact else ": ",
            sort_keys=args.sort_keys,
        )
    except ValueError as e:
        raise SystemExit(e) from None

    stdout.write(output_json)


def _main() -> None:
    try:
        parser: ArgumentParser = ArgumentParser()
        configure(parser)
        args: Any = parser.parse_args()
        run(args)
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
