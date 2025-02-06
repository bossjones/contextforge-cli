"""Base utility functions for the contextforge_cli package."""

from __future__ import annotations

import collections
import copy
import math
from typing import TYPE_CHECKING, Any

import structlog

logger = structlog.get_logger(__name__)


if TYPE_CHECKING:
    import types

SEPARATOR_CHARACTER_DEFAULT = "-"
SEPARATOR_LENGTH_DEFAULT = 40


def get_sys_module() -> types.ModuleType:
    """
    Get the 'sys' module.

    Returns:
        types.ModuleType: The 'sys' module.
    """
    import sys  # pylint:disable=reimported,import-outside-toplevel

    return sys


def get_itertools_module() -> types.ModuleType:
    """
    Get the 'itertools' module.

    Returns:
        types.ModuleType: The 'itertools' module.
    """
    import itertools  # pylint:disable=reimported,import-outside-toplevel

    return itertools


# SOURCE: https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch14s08.html
def check_whoami() -> tuple[str, int, str]:
    """
    Get information about the caller of the current function.

    By calling sys._getframe(1), you can get the function name, line number,
    and filename of the caller of the current function.

    Returns:
        Tuple[str, int, str]: A tuple containing the function name, line number,
            and filename of the caller.
    """
    sys = get_sys_module()
    this_function_name, this_line_number, this_filename = (
        sys._getframe(1).f_code.co_name,
        sys._getframe(1).f_lineno,
        sys._getframe(1).f_code.co_filename,
    )
    # logger.debug(f"{this_function_name}() @ {this_filename}:{this_line_number}")
    return this_function_name, this_line_number, this_filename


# SOURCE: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch14s08.html
def check_callersname() -> tuple[str, int, str]:
    """
    Get information about the caller of the caller of the current function.

    Returns:
        Tuple[str, int, str]: A tuple containing the function name, line number,
            and filename of the caller's caller.
    """
    sys = get_sys_module()
    this_function_name, this_line_number, this_filename = (
        sys._getframe(2).f_code.co_name,
        sys._getframe(2).f_lineno,
        sys._getframe(2).f_code.co_filename,
    )
    # logger.debug(f"{this_function_name}() @ {this_filename}:{this_line_number}")
    return this_function_name, this_line_number, this_filename
    # return sys._getframe(2).f_code.co_name


def print_line_seperator(
    value: str,
    length: int = SEPARATOR_LENGTH_DEFAULT,
    char: str = SEPARATOR_CHARACTER_DEFAULT,
) -> None:
    """
    Print a line separator with the given value centered.

    Args:
        value (str): The value to be centered in the separator.
        length (int, optional): The total length of the separator.
            Defaults to SEPARATOR_LENGTH_DEFAULT.
        char (str, optional): The character to be used for the separator.
            Defaults to SEPARATOR_CHARACTER_DEFAULT.
    """
    output = value

    if len(value) < length:
        #   Update length based on insert length, less a space for margin.
        length -= len(value) + 2
        #   Halve the length and floor left side.
        left = math.floor(length / 2)
        right = left
        #   If odd number, add dropped remainder to right side.
        if length % 2 != 0:
            right += 1

        #   Surround insert with separators.
        output = f"{char * left} {value} {char * right}"

    print_output(output)


def print_output(*args, sep: str = " ", end: str = "\n") -> None:
    """
    Print the given arguments with the specified separator and end string.

    Args:
        *args: The arguments to be printed.
        sep (str, optional): The separator between the arguments.
            Defaults to " ".
        end (str, optional): The end string to be printed after the arguments.
            Defaults to "\\n".
    """
    print(*args, sep=sep, end=end)


# SOURCE: https://gist.github.com/89465127/5776892
def create_dict_from_filter(d: dict[Any, Any], white_list: list[Any]) -> dict[Any, Any]:
    """
    Create a new dictionary by filtering the given dictionary based on a white list of keys.

    Args:
        d (Dict[Any, Any]): The dictionary to be filtered.
        white_list (List[Any]): The list of keys to be included in the new dictionary.

    Returns:
        Dict[Any, Any]: A new dictionary containing only the keys from the white list.
    """
    return {k: v for k, v in filter(lambda t: t[0] in white_list, d.items())}


# NAME: Python filter nested dict given list of key names
# https://stackoverflow.com/questions/23230947/python-filter-nested-dict-given-list-of-key-names
def fltr(
    node: dict[Any, Any] | list[Any], whitelist: list[Any]
) -> dict[Any, Any] | list[Any] | None:
    """
    Filter a nested dictionary or list based on a white list of keys.

    This function returns a new object rather than modifying the old one and
    handles filtering on non-leaf nodes.

    Args:
        node (Union[Dict[Any, Any], List[Any]]): The dictionary or list to be filtered.
        whitelist (List[Any]): The list of keys to be included in the filtered result.

    Returns:
        Union[Dict[Any, Any], List[Any], None]: The filtered dictionary, list, or None if the result is empty.

    Example:
        >>> x = {"a": 1, "b": {"c": 2, "d": 3}, "e": [{"f": 4, "g": 5}, {"h": 6}]}
        >>> fltr(x, ["a", "c", "f"])
        {'a': 1, 'b': {'c': 2}, 'e': [{'f': 4}]}
    """
    if isinstance(node, dict):
        retval = {}
        for key in node:
            if key in whitelist:
                retval[key] = copy.deepcopy(node[key])
            elif isinstance(node[key], list) or isinstance(node[key], dict):
                child = fltr(node[key], whitelist)
                if child:
                    retval[key] = child
        if retval:
            return retval
        else:
            return None
    elif isinstance(node, list):
        retval = []
        for entry in node:
            child = fltr(entry, whitelist)
            if child:
                retval.append(child)
        if retval:
            return retval
        else:
            return None


# from unittest import TestCase
# SOURCE: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dict_merge(
    dct: dict[Any, Any], merge_dct: dict[Any, Any], add_keys: bool = True
) -> dict[Any, Any]:
    """
    Recursively merge two dictionaries.

    Inspired by :meth:``dict.update()``, instead of updating only top-level keys,
    dict_merge recurses down into dicts nested to an arbitrary depth, updating keys.
    The ``merge_dct`` is merged into ``dct``.

    This version will return a copy of the dictionary and leave the original
    arguments untouched.

    The optional argument ``add_keys``, determines whether keys which are
    present in ``merge_dict`` but not ``dct`` should be included in the new dict.

    Args:
        dct (Dict[Any, Any]): The dictionary onto which the merge is executed.
        merge_dct (Dict[Any, Any]): The dictionary merged into dct.
        add_keys (bool, optional): Whether to add new keys from merge_dct that
            are not present in dct. Defaults to True.

    Returns:
        Dict[Any, Any]: The merged dictionary.
    """
    dct = dct.copy()
    if not add_keys:
        merge_dct = {k: merge_dct[k] for k in set(dct).intersection(set(merge_dct))}

    for k, v in merge_dct.items():
        if (
            k in dct
            and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.abc.Mapping)
        ):
            dct[k] = dict_merge(dct[k], merge_dct[k], add_keys=add_keys)
        else:
            dct[k] = merge_dct[k]

    return dct
