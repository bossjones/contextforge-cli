"""contextforge_cli.models.cmds"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from contextforge_cli import types


@dataclass
class CmdArgs:
    name: str


@dataclass
class DataCmd:
    name: str
    command_args: list[str] | None = []
    command_kargs: dict[str, str] = {}
