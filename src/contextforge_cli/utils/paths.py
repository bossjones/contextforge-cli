# inspired by boucanpy
from __future__ import annotations

from os.path import abspath, dirname, join

_utils_dir = abspath(dirname(__file__))


def _ajoin(target: str, path: str) -> str:
    return abspath(join(target, path))
