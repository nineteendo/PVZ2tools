#!/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""JSON tool."""
from __future__ import annotations

__all__: list[str] = ["JSONNamespace", "register", "run"]

import sys
from argparse import ArgumentParser
from pathlib import Path
from sys import stderr, stdin

from jsonyx import JSONSyntaxError, dump, format_syntax_error, loads
from jsonyx.allow import EVERYTHING, NOTHING, SURROGATES


# pylint: disable-next=R0903
class JSONNamespace:
    """JSON namespace."""

    compact: bool
    ensure_ascii: bool
    indent: int | str | None
    filename: str | None
    no_commas: bool
    nonstrict: bool
    sort_keys: bool
    trailing_comma: bool
    use_decimal: bool


def register(parser: ArgumentParser) -> None:
    """Register JSON tool.

    :param parser: an argument parser
    :type parser: ArgumentParser
    """
    parser.add_argument(
        "filename",
        nargs="?",
        help="the JSON file to be validated or pretty-printed",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help='don\'t add unnecessary whitespace after "," and ":"',
    )
    parser.add_argument(
        "--ensure-ascii",
        action="store_true",
        help="escape non-ascii characters",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--indent", type=int, metavar="SPACES", help="indent using spaces",
    )
    group.add_argument(
        "--indent-tab", action="store_const", const="\t", dest="indent",
        help="indent using tabs",
    )
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument(
        "--no-commas",
        action="store_true",
        help="separate items by whitespace",
    )
    group2.add_argument(
        "--trailing-comma",
        action="store_true",
        help="add a trailing comma if indented",
    )
    parser.add_argument(
        "--nonstrict", action="store_true", help="allow all JSON deviations",
    )
    parser.add_argument(
        "--sort-keys", action="store_true", help="sort the keys of objects",
    )
    parser.add_argument(
        "--use-decimal",
        action="store_true",
        help="use decimal instead of float",
    )


def run(args: JSONNamespace) -> None:
    """Run JSON tool.

    :param args: the commandline arguments
    :type args: JSONNamespace
    """
    if args.filename:
        filename: str = args.filename
        s: bytes | str = Path(filename).read_bytes()
    else:
        filename = "<stdin>"
        s = "\n".join(
            iter(input, ""),
        ) if stdin.isatty() else stdin.buffer.read()

    try:
        obj: object = loads(
            s,
            allow=EVERYTHING - SURROGATES if args.nonstrict else NOTHING,
            filename=filename,
            use_decimal=args.use_decimal,
        )
    except JSONSyntaxError as exc:
        stderr.write("".join(format_syntax_error(exc)))
        sys.exit(1)

    dump(
        obj,
        allow=EVERYTHING - SURROGATES if args.nonstrict else NOTHING,
        ensure_ascii=args.ensure_ascii,
        indent=args.indent,
        item_separator=" " if args.no_commas else (
            "," if args.compact else ", "
        ),
        key_separator=":" if args.compact else ": ",
        sort_keys=args.sort_keys,
        trailing_comma=args.trailing_comma,
    )


def _main() -> None:
    parser: ArgumentParser = ArgumentParser()
    register(parser)
    try:
        run(parser.parse_args(namespace=JSONNamespace()))
    except BrokenPipeError as exc:
        sys.exit(exc.errno)


if __name__ == "__main__":
    _main()
