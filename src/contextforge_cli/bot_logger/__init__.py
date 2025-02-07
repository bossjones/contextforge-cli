# #!/usr/bin/env python3
# pylint: disable=no-member

from __future__ import annotations

import logging

import structlog

from contextforge_cli.models.loggers import LoggerModel, LoggerPatch

logger = structlog.get_logger(__name__)


def get_lm_from_tree(loggertree: LoggerModel, find_me: str) -> LoggerModel | None:
    """Recursively search for a logger model in the logger tree.

    Args:
        loggertree: The root logger model to search from.
        find_me: The name of the logger model to find.

    Returns:
        The found logger model, or None if not found.
    """
    if find_me == loggertree.name:
        print("Found")
        return loggertree
    else:
        for ch in loggertree.children:
            print(f"Looking in: {ch.name}")
            if i := get_lm_from_tree(ch, find_me):
                return i
    return None


def generate_tree() -> LoggerModel:
    """Generate a tree of logger models.

    Returns:
        The root logger model of the generated tree.
    """
    rootm = LoggerModel(
        name="root", level=logging.getLogger().getEffectiveLevel(), children=[]
    )
    nodesm: dict[str, LoggerModel] = {}
    items = sorted(logging.root.manager.loggerDict.items())  # type: ignore
    for name, loggeritem in items:
        if isinstance(loggeritem, logging.PlaceHolder):
            nodesm[name] = nodem = LoggerModel(name=name, children=[])
        else:
            nodesm[name] = nodem = LoggerModel(
                name=name, level=loggeritem.getEffectiveLevel(), children=[]
            )
        i = name.rfind(".", 0, len(name) - 1)
        parentm = rootm if i == -1 else nodesm[name[:i]]
        parentm.children.append(nodem)
    return rootm
