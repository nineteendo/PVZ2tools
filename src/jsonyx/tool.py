#!/usr/bin/env python
# Copyright (C) 2024 Nice Zombies
"""JSON tool."""
from __future__ import annotations

__all__: list[str] = ["JSONNamespace", "register", "run"]

import sys
from argparse import ArgumentParser
from pathlib import Path
from sys import stdin

from jsonyx import JSONSyntaxError, dump, format_syntax_error, loads
from jsonyx.allow import EVERYTHING, NOTHING, SURROGATES
from typing_extensions import Any  # type: ignore


class JSONNamespace:  # pylint: disable=R0903
    """JSON namespace."""

    compact: bool
    ensure_ascii: bool
    indent: int | str | None
    filename: str | None
    no_commas: bool
    nonstrict: bool
    sort_keys: bool
    use_decimal: bool


def register(parser: ArgumentParser) -> None:
    """Register JSON tool."""
    parser.add_argument("filename", nargs="?")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--ensure-ascii", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--indent", type=int, metavar="SPACES")
    group.add_argument(
        "--indent-tab", action="store_const", const="\t", dest="indent",
    )
    parser.add_argument("--no-commas", action="store_true")
    parser.add_argument("--nonstrict", action="store_true")
    parser.add_argument("--sort-keys", action="store_true")
    parser.add_argument("--use-decimal", action="store_true")


def run(args: JSONNamespace) -> None:
    """Run JSON tool."""
    if args.filename:
        filename: str = args.filename
        s: bytes | str = Path(filename).read_bytes()
    else:
        filename = "<stdin>"
        s = "\n".join(
            iter(input, ""),
        ) if stdin.isatty() else stdin.buffer.read()

    try:
        obj: Any = loads(
            s,
            allow=EVERYTHING - SURROGATES if args.nonstrict else NOTHING,
            filename=filename,
            use_decimal=args.use_decimal,
        )
    except JSONSyntaxError as exc:
        raise SystemExit(format_syntax_error(exc)) from None

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
