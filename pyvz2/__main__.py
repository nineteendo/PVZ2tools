#!/usr/bin/env python
"""PyVZ2, a command line utility to modify PVZ2."""
# Copyright (C) 2020-2024 Nice Zombies
# TODO(Nice Zombies): Interactive menus
# TODO(Nice Zombies): Update checking
# TODO(Nice Zombies): Custom keyboard shortcuts
# TODO(Nice Zombies): Built-in file manager
# TODO(Nice Zombies): PathPicker error logging
# TODO(Nice Zombies): CLInteract unit tests
# TODO(Nice Zombies): Open folder command
# TODO(Nice Zombies): CLInteract demo
# TODO(Nice Zombies): CLInteract translations
# TODO(Nice Zombies): Libraries documentation
# TODO(Nice Zombies): Reimplement old functionality
# TODO(Nice Zombies): Error logging
# TODO(Nice Zombies): Unit tests
# TODO(Nice Zombies): Command line arguments
# TODO(Nice Zombies): Translations
# TODO(Nice Zombies): Documentation
from __future__ import annotations

__all__: list[str] = []
__author__: str = "Nice Zombies"
__version__: str = "2.0"

from argparse import ArgumentParser
from contextlib import chdir, suppress
from gettext import gettext as _
from logging import DEBUG, INFO, basicConfig, exception, info
from logging.handlers import RotatingFileHandler
from sys import stderr
from typing import TYPE_CHECKING, Literal, assert_never

from ansio import (
    application_keypad, colored_output, mouse_input, no_cursor, raw_input,
)
from ansio.input import EndOfStdinError, get_input_event
from clinteract import input_str
from fsys import RES_DIR

if TYPE_CHECKING:
    from pathlib import Path

_LOG_DIR: Path = RES_DIR / "logs"
_LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
_LOG_SIZE: int = 5 * 1024 * 1024


class PyVZ2Namespace:  # pylint: disable=too-few-public-methods
    """Namespace of PyVZ2."""

    command: Literal["keyboard"] | None
    verbose: bool


def main() -> None:
    """Start PyVZ2."""
    parser: ArgumentParser = ArgumentParser(
        description="PyVZ2, a command line utility to modify PVZ2",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s v{__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable verbose logging",
    )
    commands = parser.add_subparsers(dest="command", help="command")
    commands.add_parser("keyboard", help="print keyboard events")
    args: PyVZ2Namespace = parser.parse_args(namespace=PyVZ2Namespace())
    _LOG_DIR.mkdir(exist_ok=True)
    handler: RotatingFileHandler = RotatingFileHandler(
        _LOG_DIR / "pyvz2.log",
        maxBytes=_LOG_SIZE,
        backupCount=1,
    )
    basicConfig(
        format=_LOG_FORMAT,
        level=DEBUG if args.verbose else INFO,
        handlers=[handler],
    )
    info("Program started")
    try:
        with chdir(RES_DIR), suppress(EndOfStdinError, KeyboardInterrupt):
            if args.command is None:
                input_str(_("Enter a string:"))
            elif args.command == "keyboard":
                with (
                    raw_input, application_keypad, mouse_input, colored_output,
                    no_cursor,
                ):
                    while True:
                        print(repr(get_input_event().shortcut))
            else:
                assert_never(args.command)
    except Exception as err:  # pylint: disable=broad-exception-caught
        exception("Unexpected error")
        print(f"{type(err).__name__}: {err}", file=stderr)
        print(f"Please refer to {_LOG_DIR}", file=stderr)


if __name__ == "__main__":
    main()