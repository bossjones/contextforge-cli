"""Miscellaneous utility functions."""

# SOURCE: https://github.com/napari/napari/blob/6ce45aed3c893c03a47dc1d743e43b342b7022cb/napari/utils/misc.py#L400
# pylint: disable=no-member
from __future__ import annotations

import builtins
import contextlib
import importlib.metadata
import inspect
import itertools
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from os import PathLike, fspath, path
from os import path as os_path
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

import numpy as np

if TYPE_CHECKING:
    import packaging.version


ROOT_DIR = path.dirname(path.dirname(__file__))


def parse_version(v: str) -> packaging.version._BaseVersion:
    """
    Parse a version string and return a packaging.version.Version obj.

    Args:
        v (str): The version string to parse.

    Returns:
        packaging.version._BaseVersion: The parsed version object.
    """
    import packaging.version

    try:
        return packaging.version.Version(v)
    except packaging.version.InvalidVersion:
        return packaging.version.LegacyVersion(v)  # type: ignore[attr-defined]


def running_as_bundled_app() -> bool:
    """
    Infer whether we are running as a briefcase bundle.

    Returns:
        bool: True if running as a bundled app, False otherwise.
    """
    # https://github.com/beeware/briefcase/issues/412
    # https://github.com/beeware/briefcase/pull/425
    # note that a module may not have a __package__ attribute
    # From 0.4.12 we add a sentinel file next to the bundled sys.executable
    if (Path(sys.executable).parent / ".napari_is_bundled").exists():
        return True

    try:
        app_module = sys.modules["__main__"].__package__
    except AttributeError:
        return False

    if not app_module:
        return False

    try:
        metadata = importlib.metadata.metadata(app_module)
    except importlib.metadata.PackageNotFoundError:
        return False

    return "Briefcase-Version" in metadata


def bundle_bin_dir() -> str | None:
    """
    Return path to briefcase app_packages/bin if it exists.

    Returns:
        Optional[str]: The path to the bin directory if it exists, None otherwise.
    """
    path_to_bin: builtins.str = os_path.join(
        os_path.dirname(sys.exec_prefix), "app_packages", "bin"
    )
    if path.isdir(path_to_bin):
        return f"{path_to_bin}"
    return None


def str_to_rgb(arg: str) -> list[int]:
    """
    Convert an rgb string 'rgb(x,y,z)' to a list of ints [x,y,z].

    Args:
        arg (str): The RGB string to convert.

    Returns:
        list[int]: The RGB values as a list of integers.
    """
    return list(map(int, re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", arg).groups()))


def ensure_iterable(arg: Any, color: bool = False) -> Iterable:
    """
    Ensure an argument is an iterable. Useful when an input argument
    can either be a single value or a list. If a color is passed then it
    will be treated specially to determine if it is iterable.

    Args:
        arg (Any): The argument to check for iterability.
        color (bool, optional): Whether the argument represents a color. Defaults to False.

    Returns:
        Iterable: The input as an iterable.
    """
    return arg if is_iterable(arg, color=color) else itertools.repeat(arg)


def is_iterable(arg: Any, color: bool = False) -> bool:
    """
    Determine if a single argument is an iterable. If a color is being
    provided and the argument is a 1-D array of length 3 or 4 then the input
    is taken to not be iterable.

    Args:
        arg (Any): The argument to check for iterability.
        color (bool, optional): Whether the argument represents a color. Defaults to False.

    Returns:
        bool: True if the argument is iterable, False otherwise.
    """
    if arg is None or type(arg) is str or np.isscalar(arg):
        return False
    elif color and isinstance(arg, (list, np.ndarray)):
        return np.array(arg).ndim != 1 or len(arg) not in [3, 4]
    else:
        return True


def is_sequence(arg: Any) -> bool:
    """
    Check if ``arg`` is a sequence like a list or tuple.

    Args:
        arg (Any): The argument to check.

    Returns:
        bool: True if the argument is a sequence, False otherwise.
    """
    return isinstance(arg, Sequence) and not isinstance(arg, str)


def ensure_sequence_of_iterables(obj: Any, length: int | None = None) -> Iterable:
    """
    Ensure that ``obj`` behaves like a (nested) sequence of iterables.

    If length is provided and the object is already a sequence of iterables,
    a ValueError will be raised if ``len(obj) != length``.

    Args:
        obj (Any): The object to check.
        length (int, optional): Expected length of the sequence. Defaults to None.

    Returns:
        Iterable: A nested sequence of iterables, or an itertools.repeat instance.

    Raises:
        ValueError: If length is provided and the object's length does not match.
    """
    if obj is not None and is_sequence(obj) and is_iterable(obj[0]):
        if length is not None and len(obj) != length:
            raise ValueError(f"length of {obj} must equal {length}")
        return obj
    return itertools.repeat(obj)


def formatdoc(obj: Any) -> Any:
    """
    Substitute globals and locals into an object's docstring.

    Args:
        obj (Any): The object to format the docstring for.

    Returns:
        Any: The input object with the formatted docstring.
    """
    frame = inspect.currentframe().f_back
    try:
        obj.__doc__ = obj.__doc__.format(**{**frame.f_globals, **frame.f_locals})
        return obj
    finally:
        del frame


camel_to_snake_pattern = re.compile(r"(.)([A-Z][a-z]+)")
camel_to_spaces_pattern = re.compile(r"((?<=[a-z])[A-Z]|(?<!\A)[A-R,T-Z](?=[a-z]))")


def camel_to_snake(name: str) -> str:
    """
    Convert a camel case string to snake case.

    Args:
        name (str): The camel case string to convert.

    Returns:
        str: The snake case string.
    """
    return camel_to_snake_pattern.sub(r"\1_\2", name).lower()


def camel_to_spaces(val: str) -> str:
    """
    Convert a camel case string to a string with spaces before uppercase letters.

    Args:
        val (str): The camel case string to convert.

    Returns:
        str: The string with spaces added.
    """
    return camel_to_spaces_pattern.sub(r" \1", val)


T = TypeVar("T", str, Sequence[str])


def abspath_or_url(relpath: T) -> T:
    """
    Utility function that normalizes paths or a sequence thereof.

    Expands user directory and converts relpaths to abspaths... but ignores
    URLS that begin with "http", "ftp", or "file".

    Args:
        relpath (str or Sequence[str]): A path, or list or tuple of paths.

    Returns:
        str or Sequence[str]: An absolute path, or list or tuple of absolute paths (same type as input).

    Raises:
        TypeError: If the input is not a string, PathLike, or sequence thereof.
    """
    from urllib.parse import urlparse

    if isinstance(relpath, (tuple, list)):
        return type(relpath)(abspath_or_url(p) for p in relpath)

    if isinstance(relpath, (str, PathLike)):
        relpath = fspath(relpath)
        urlp = urlparse(relpath)
        if urlp.scheme and urlp.netloc:
            return relpath
        return path.abspath(path.expanduser(relpath))

    raise TypeError("Argument must be a string, PathLike, or sequence thereof")


class CallDefault(inspect.Parameter):
    def __str__(self) -> str:
        """
        Wrap defaults in a string representation.

        Returns:
            str: The string representation of the parameter with wrapped defaults.
        """
        kind = self.kind
        formatted = self.name

        # Fill in defaults
        if self.default is not inspect._empty or kind == inspect.Parameter.KEYWORD_ONLY:
            formatted = f"{formatted}={formatted}"

        if kind == inspect.Parameter.VAR_POSITIONAL:
            formatted = f"*{formatted}"
        elif kind == inspect.Parameter.VAR_KEYWORD:
            formatted = f"**{formatted}"

        return formatted


class CallSignature(inspect.Signature):
    _parameter_cls = CallDefault

    def __str__(self) -> str:
        """
        Return a string representation of the signature without separators.

        Returns:
            str: The string representation of the signature.
        """
        result = [str(param) for param in self.parameters.values()]
        rendered = f"({', '.join(result)})"

        if self.return_annotation is not inspect._empty:
            anno = inspect.formatannotation(self.return_annotation)
            rendered += f" -> {anno}"

        return rendered


callsignature = CallSignature.from_callable


def all_subclasses(cls: type) -> set[type]:
    """
    Recursively find all subclasses of class ``cls``.

    Args:
        cls (type): A python class (or anything that implements a __subclasses__ method).

    Returns:
        set[type]: The set of all classes that are subclassed from ``cls``.
    """
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)]
    )


def ensure_n_tuple(val: Iterable, n: int, fill: Any = 0) -> tuple:
    """
    Ensure input is a length n tuple.

    Args:
        val (Iterable): Iterable to be forced into length n-tuple.
        n (int): Length of tuple.
        fill (Any, optional): Fill value for missing elements. Defaults to 0.

    Returns:
        tuple: Coerced tuple.

    Raises:
        AssertionError: If n is not greater than 0.
    """
    assert n > 0, "n must be greater than 0"
    tuple_value = tuple(val)
    return (fill,) * (n - len(tuple_value)) + tuple_value[-n:]


def ensure_layer_data_tuple(val: Any) -> tuple:
    """
    Ensure input is a valid layer data tuple.

    Args:
        val (Any): The value to check.

    Returns:
        tuple: The input as a valid layer data tuple.

    Raises:
        TypeError: If the input is not a valid layer data tuple.
    """
    if not (isinstance(val, tuple) and (0 < len(val) <= 3)):
        raise TypeError(f"Not a valid layer data tuple: {val!r}")
    return val


def ensure_list_of_layer_data_tuple(val: Any) -> list[tuple]:
    """
    Ensure input is a valid list of layer data tuples.

    Args:
        val (Any): The value to check.

    Returns:
        list[tuple]: The input as a valid list of layer data tuples.

    Raises:
        TypeError: If the input is not a valid list of layer data tuples.
    """
    if isinstance(val, list) and len(val):
        with contextlib.suppress(TypeError):
            return [ensure_layer_data_tuple(v) for v in val]
    raise TypeError("Not a valid list of layer data tuples!")


def yesno(question: str, force: bool = False) -> bool:
    """
    Simple Yes/No prompt.

    Args:
        question (str): The question to ask.
        force (bool, optional): Whether to force a yes response. Defaults to False.

    Returns:
        bool: True if the user responds 'y', False if 'n'.
    """
    prompt = f"{question} ? (y/n): "
    ans = input(prompt).strip().lower()
    if ans not in ["y", "n"] and not force:
        print(f"{ans} is invalid, please try again...")
        return yesno(question)
    return ans == "y" or force


def divide_chunks(l: list[str], n: int = 10) -> Iterable[list[str]]:
    """
    Yield successive n-sized chunks from list l.

    Args:
        l (list[str]): The list to divide into chunks.
        n (int, optional): The size of each chunk. Defaults to 10.

    Yields:
        Iterable[list[str]]: Successive n-sized chunks from the input list.
    """
    for i in range(0, len(l), n):
        yield l[i : i + n]


CURRENTFUNCNAME: Callable[[int], str] = lambda n=0: sys._getframe(n + 1).f_code.co_name
"""
Get the name of the current function, or the name of the caller of the current function.

Args:
    n (int, optional): The number of frames to go back. Defaults to 0.
        0 returns the name of the current function.
        1 returns the name of the caller of the current function, etc.

Returns:
    str: The name of the requested function.
"""
