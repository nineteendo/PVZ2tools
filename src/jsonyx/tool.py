# Copyright (C) 2024 Nice Zombies
"""JSON tool."""
from __future__ import annotations

__all__: list[str] = ["JSONNamespace", "register", "run"]

import sys
from sys import stderr, stdin
from typing import TYPE_CHECKING

from jsonyx import Decoder, Encoder, JSONSyntaxError, format_syntax_error
from jsonyx.allow import EVERYTHING, NOTHING

if TYPE_CHECKING:
    from argparse import ArgumentParser


# pylint: disable-next=R0903
class JSONNamespace:
    """JSON namespace."""

    compact: bool
    ensure_ascii: bool
    indent: int | str | None
    input_filename: str | None
    no_commas: bool
    nonstrict: bool
    output_filename: str | None
    sort_keys: bool
    trailing_comma: bool
    use_decimal: bool


def register(parser: ArgumentParser) -> None:
    """Register JSON tool.

    :param parser: an argument parser
    :type parser: ArgumentParser
    """
    parser.add_argument(
        "-a",
        "--ensure-ascii",
        action="store_true",
        help="escape non-ascii characters",
    )
    parser.add_argument(
        "-c",
        "--compact",
        action="store_true",
        help='don\'t add unnecessary whitespace after "," and ":"',
    )
    comma_group = parser.add_mutually_exclusive_group()
    comma_group.add_argument(
        "-C",
        "--no-commas",
        action="store_true",
        help="separate items by whitespace instead of comma's",
    )
    parser.add_argument(
        "-d",
        "--use-decimal",
        action="store_true",
        help="use decimal instead of float",
    )
    indent_group = parser.add_mutually_exclusive_group()
    indent_group.add_argument(
        "-i",
        "--indent",
        type=int,
        metavar="SPACES",
        help="indent using spaces",
    )
    parser.add_argument(
        "-s",
        "--sort-keys",
        action="store_true",
        help="sort the keys of objects",
    )
    parser.add_argument(
        "-S",
        "--nonstrict",
        action="store_true",
        help="allow all JSON deviations",
    )
    comma_group.add_argument(
        "-t",
        "--trailing-comma",
        action="store_true",
        help="add a trailing comma if indented",
    )
    indent_group.add_argument(
        "-T",
        "--indent-tab",
        action="store_const",
        const="\t",
        dest="indent",
        help="indent using tabs",
    )
    parser.add_argument(
        "input_filename",
        nargs="?",
        help='the path to the input JSON file, or "-" for standard input',
    )
    parser.add_argument(
        "output_filename",
        nargs="?",
        help="the path to the output JSON file",
    )


def run(args: JSONNamespace) -> None:
    """Run JSON tool.

    :param args: the commandline arguments
    :type args: JSONNamespace
    """
    decoder: Decoder = Decoder(
        allow=EVERYTHING if args.nonstrict else NOTHING,
        use_decimal=args.use_decimal,
    )
    encoder: Encoder = Encoder(
        allow=EVERYTHING if args.nonstrict else NOTHING,
        ensure_ascii=args.ensure_ascii,
        indent=args.indent,
        item_separator=" " if args.no_commas else (
            "," if args.compact else ", "
        ),
        key_separator=":" if args.compact else ": ",
        sort_keys=args.sort_keys,
        trailing_comma=args.trailing_comma,
    )
    try:
        if args.input_filename and args.input_filename != "-":
            obj: object = decoder.read(args.input_filename)
        elif stdin.isatty():
            obj = decoder.loads("\n".join(iter(input, "")), filename="<stdin>")
        else:
            obj = decoder.load(stdin)
    except JSONSyntaxError as exc:
        stderr.write("".join(format_syntax_error(exc)))
        sys.exit(1)

    if args.output_filename:
        encoder.write(obj, args.output_filename)
    else:
        encoder.dump(obj)
