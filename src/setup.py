# Copyright (C) 2024 Nice Zombies
"""Dependencies of PyVZ2."""
from __future__ import annotations

__all__: list[str] = []

# pylint: disable-next=E0401
from setuptools import (  # type: ignore
    Extension, find_namespace_packages, setup,
)

if __name__ == "__main__":
    setup(
        name="pyvz2-dependencies",
        version="0.0.1",
        packages=find_namespace_packages(),
        ext_modules=[Extension(
            "_jsonyx.__init__", ["_jsonyx/__init__.c"], optional=True,
        )],
        # TODO(Nice Zombies): add jsonyx as a dependency
        install_requires=["typing_extensions"],
    )
