#!/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""JSON tool."""
from __future__ import annotations

__all__ = ["JSONNamespace", "register", "run"]

import sys
from argparse import ArgumentParser
from pathlib import Path
from sys import stdin

from jsonyx import dumps, loads
from jsonyx.scanner import JSONSyntaxError, format_error
from typing_extensions import Any  # type: ignore


class JSONNamespace:  # pylint: disable=R0903
    """JSON namespace."""

    compact: bool
    ensure_ascii: bool
    indent: int | str | None
    filename: str | None
    nonstrict: bool


def register(parser: ArgumentParser) -> None:
    """Register JSON tool."""
    parser.add_argument("filename", nargs="?")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--ensure-ascii", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--indent", type=int, metavar="SPACES")
    group.add_argument(
        "--tab",
        action="store_const",
        const="\t",
        dest="indent",
        help="indent with tabs",
    )
    parser.add_argument("--nonstrict", action="store_true")


def run(args: JSONNamespace) -> None:
    """Run JSON tool."""
    input_json: bytes | str
    if args.filename:
        filename: str = args.filename
        input_json = Path(filename).read_bytes()
    elif stdin.isatty():
        filename, input_json = "<stdin>", "\n".join(iter(input, ""))
    else:
        filename, input_json = "<stdin>", stdin.buffer.read()

    try:
        obj: Any = loads(
            input_json,
            allow=[
                "comments", "duplicate_keys", "nan", "trailing_comma",
            ] if args.nonstrict else [],
            filename=filename,
        )
    except JSONSyntaxError as exc:
        raise SystemExit(format_error(exc)) from None

    output_json: str = dumps(
        obj,
        allow=["nan"] if args.nonstrict else [],
        ensure_ascii=args.ensure_ascii,
        indent=args.indent,
        item_separator="," if args.compact else ", ",
        key_separator=":" if args.compact else ": ",
    )
    print(output_json)


def _main() -> None:
    parser: ArgumentParser = ArgumentParser()
    register(parser)
    try:
        run(parser.parse_args(namespace=JSONNamespace()))
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
