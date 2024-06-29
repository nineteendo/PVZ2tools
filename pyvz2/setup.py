"""Dependencies of PyVZ2."""
# Copyright (C) 2024 Nice Zombies
from __future__ import annotations

__all__: list[str] = []

# mypy: disable-error-code=import-untyped
from setuptools import Extension, find_packages, setup

if __name__ == "__main__":
    setup(
        name="pyvz2-dependencies",
        version="0.1.0",
        packages=find_packages(),  # Exclude forked packages
        py_modules=[],  # Include python modules
        ext_modules=[Extension("_hello", ["hello/_hello.c"])],
        requires=[],  # Include forked packages
    )
