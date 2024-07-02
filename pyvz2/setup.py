"""Dependencies of PyVZ2."""
# Copyright (C) 2024 Nice Zombies
from __future__ import annotations

__all__: list[str] = []

# pylint: disable=import-error
from setuptools import Extension, find_packages, setup  # type: ignore

if __name__ == "__main__":
    setup(
        name="pyvz2",
        version="0.1.0",
        packages=find_packages(),
        ext_modules=[Extension("_jsonc", ["jsonc/_accelerator.c"])],
    )
