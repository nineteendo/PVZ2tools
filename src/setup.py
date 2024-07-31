# Copyright (C) 2024 Nice Zombies
"""Dependencies of PyVZ2."""
from __future__ import annotations

__all__: list[str] = []

# pylint: disable-next=E0401
from setuptools import Extension, find_packages, setup  # type: ignore

if __name__ == "__main__":
    setup(
        name="pyvz2-dependencies",
        version="0.0.1",
        packages=find_packages(),
        ext_modules=[
            Extension("_jsonyx", ["jsonyx/_speedups.c"], optional=True),
        ],
        # TODO(Nice Zombies): add jsonyx as a dependency
        install_requires=["typing_extensions"],
    )
